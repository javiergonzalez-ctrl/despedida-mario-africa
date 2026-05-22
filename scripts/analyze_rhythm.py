"""
Generate a beatMap for the rhythm mini-game from cara-al-sol.mp3.

Beat-aligned approach (the canonical librosa pipeline):
  1. Compute onset strength envelope.
  2. Run beat_track to lock the song's tempo grid (BPM + beat times).
  3. Run onset_detect for the raw accents.
  4. SNAP each onset to its nearest beat. Only keep onsets that match a beat
     within SNAP_TOLERANCE_MS — that's what makes the chart feel "on beat"
     instead of jittery.
  5. Optionally subdivide beats into half-beats / quarter-beats if the song
     has lots of accents between main beats.
  6. Assign lane via spectral centroid (low pitch -> left, high -> right).
  7. Detect HOLDS where consecutive beat slots have one strong onset followed
     by sustained energy with no new onset.
  8. Detect DOUBLES for the strongest accented beats.

This replaces the previous "every onset becomes a note" approach which made
the start feel jittery — multiple sub-syllable onsets in a single beat slot.
Now we get one well-placed note per beat (or per sub-beat).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "cara-al-sol.mp3"
OUT_JSON = Path(__file__).with_name("beatmap.json")

START_AT_MS = 1500
STOP_AT_MS = 55_000
SUBDIVISIONS = 2          # 1 = note per beat, 2 = also half-beats, 4 = quarter
SNAP_TOLERANCE_MS = 110   # onset must be within this of a (sub)beat to qualify
MIN_GAP_MS = 130          # global minimum gap (any lane)
MIN_SAME_LANE_GAP_MS = 400  # minimum gap between consecutive notes in the SAME lane
HOLD_TAIL_BUFFER_MS = 260   # how long after a hold ends before same lane can fire
CLUSTER_MS = 320            # within this window, every note must be on a different lane

HOLD_MIN_MS = 600
HOLD_CAP_MS = 1400
DOUBLE_RATIO = 0.10
DOUBLE_STRENGTH_PCT = 0.75


def analyse(audio_path: Path) -> list[dict]:
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    duration_ms = int(librosa.get_duration(y=y, sr=sr) * 1000)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, units="frames",
        backtrack=False, delta=0.06, wait=2,
    )
    onset_times_ms = (librosa.frames_to_time(onset_frames, sr=sr) * 1000).astype(int)
    onset_strengths = onset_env[onset_frames]
    print(f"[info] {len(onset_frames)} raw onsets", file=sys.stderr)

    # Beat tracking — locks the BPM grid of the song
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, units="frames"
    )
    if hasattr(tempo, "item"):
        tempo = float(tempo.item() if tempo.size == 1 else tempo[0])
    beat_times_ms = (librosa.frames_to_time(beat_frames, sr=sr) * 1000).astype(int)
    print(f"[info] tempo={tempo:.1f} BPM, {len(beat_times_ms)} beats", file=sys.stderr)

    # Subdivide beats — insert intermediate "sub-beats" between each consecutive
    # pair, so onsets that fall halfway through a beat still get snapped.
    if SUBDIVISIONS > 1 and len(beat_times_ms) > 1:
        grid = []
        for i in range(len(beat_times_ms) - 1):
            grid.append(int(beat_times_ms[i]))
            for s in range(1, SUBDIVISIONS):
                grid.append(int(beat_times_ms[i] + (beat_times_ms[i+1] - beat_times_ms[i]) * s / SUBDIVISIONS))
        grid.append(int(beat_times_ms[-1]))
        grid = np.array(grid, dtype=int)
    else:
        grid = beat_times_ms.copy()
    print(f"[info] grid (after x{SUBDIVISIONS}): {len(grid)} slots", file=sys.stderr)

    # Spectral centroid and bandwidth for later lane / double decisions
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]

    # Snap each ONSET to its nearest grid slot. Keep the strongest onset per slot.
    # If no onset is close to a slot, that slot becomes empty (no note).
    slot_data = {}  # slot_ms -> (strength, centroid, bandwidth)
    for ms, strength, frame_idx in zip(onset_times_ms, onset_strengths, onset_frames):
        if ms < START_AT_MS or ms > STOP_AT_MS:
            continue
        # nearest grid slot
        idx = int(np.argmin(np.abs(grid - ms)))
        slot_ms = int(grid[idx])
        if abs(slot_ms - ms) > SNAP_TOLERANCE_MS:
            continue
        cent = float(centroid[min(frame_idx, len(centroid) - 1)])
        bw = float(bandwidth[min(frame_idx, len(bandwidth) - 1)])
        if slot_ms not in slot_data or strength > slot_data[slot_ms][0]:
            slot_data[slot_ms] = (float(strength), cent, bw)

    print(f"[info] {len(slot_data)} slots have onsets", file=sys.stderr)

    # Sort by time
    slots = sorted(slot_data.items())  # [(ms, (strength, cent, bw)), ...]

    # Enforce MIN_GAP_MS — drop the weaker of a too-close pair
    filtered = []
    for ms, (s, c, bw) in slots:
        if filtered and ms - filtered[-1][0] < MIN_GAP_MS:
            # Replace previous if this one is stronger
            if s > filtered[-1][1][0]:
                filtered[-1] = (ms, (s, c, bw))
            continue
        filtered.append((ms, (s, c, bw)))
    print(f"[info] {len(filtered)} slots after min-gap filter", file=sys.stderr)

    if not filtered:
        return []

    # Lane assignment from centroid (normalised across kept slots)
    cents = np.array([d[1][1] for d in filtered])
    if cents.max() == cents.min():
        lane_norm = np.zeros_like(cents)
    else:
        lane_norm = (cents - cents.min()) / (cents.max() - cents.min())
    lanes = np.clip((lane_norm * 4).astype(int), 0, 3)

    # Anti-repeat: no >2 consecutive same lane
    last, run = -1, 0
    for i in range(len(lanes)):
        if lanes[i] == last:
            run += 1
            if run >= 2:
                lanes[i] = (int(lanes[i]) + 1) % 4
                run = 0
        else:
            run = 0
        last = int(lanes[i])

    # Detect holds: when the next slot is far AND the onset envelope between
    # them stays above the local mean, mark the current slot as a hold.
    holds = [0] * len(filtered)
    env_mean = onset_env.mean()
    for i in range(len(filtered) - 1):
        gap = filtered[i+1][0] - filtered[i][0]
        if gap >= HOLD_MIN_MS:
            f_now = librosa.time_to_frames(filtered[i][0] / 1000.0, sr=sr)
            f_next = librosa.time_to_frames(filtered[i+1][0] / 1000.0, sr=sr)
            if f_next > f_now:
                seg = onset_env[f_now:f_next]
                if seg.size > 2 and seg.mean() > env_mean * 0.55:
                    holds[i] = min(gap - 200, HOLD_CAP_MS)

    # Detect doubles for very strong + wide-band slots
    strengths = np.array([d[1][0] for d in filtered])
    bws = np.array([d[1][2] for d in filtered])
    s_thr = np.quantile(strengths, DOUBLE_STRENGTH_PCT)
    bw_thr = np.quantile(bws, DOUBLE_STRENGTH_PCT)
    rng = np.random.default_rng(7)

    out = []
    last_dbl = -10
    for i, ((ms, _), lane, hold) in enumerate(zip(filtered, lanes, holds)):
        note = {"t": int(ms), "lane": int(lane)}
        if hold > 0:
            note["dur"] = int(hold)
        out.append(note)
        eligible = (strengths[i] >= s_thr and bws[i] >= bw_thr and (i - last_dbl) >= 4)
        if eligible and rng.random() < DOUBLE_RATIO:
            choices = [l for l in range(4) if l != int(lane)]
            choices.sort(key=lambda l: -abs(l - int(lane)))
            paired = int(choices[0])
            second = {"t": int(ms), "lane": paired}
            if hold > 0:
                second["dur"] = int(hold)
            out.append(second)
            last_dbl = i

    out.sort(key=lambda n: (n["t"], n["lane"]))

    # === PHYSICAL PLAYABILITY PASS ===
    # Walk the chart in time order. Two rules:
    #   (a) Same-lane spacing: the same lane can't fire within MIN_SAME_LANE_GAP
    #       of its last tap, or while its previous hold tail (+ buffer) is alive.
    #   (b) Cluster rule: notes within CLUSTER_MS of EACH OTHER must use four
    #       different lanes (no repeats inside a fast cluster).
    # If a wanted lane is blocked, hop to the nearest free lane.
    lane_busy_until = [0, 0, 0, 0]
    recent_window: list[tuple[int, int]] = []  # [(t, lane), ...] for cluster check
    for n in out:
        t = n["t"]
        wanted = n["lane"]
        # Trim recent_window
        recent_window = [(rt, rl) for (rt, rl) in recent_window if t - rt <= CLUSTER_MS]
        cluster_lanes = {rl for (_rt, rl) in recent_window}
        # Eligible lane: (a) free for same-lane spacing AND (b) not in cluster
        candidates = sorted(range(4), key=lambda L: (abs(L - wanted), L))
        chosen = None
        for L in candidates:
            if t >= lane_busy_until[L] and L not in cluster_lanes:
                chosen = L
                break
        if chosen is None:
            # Relax cluster rule first
            for L in candidates:
                if t >= lane_busy_until[L]:
                    chosen = L
                    break
        if chosen is None:
            chosen = min(range(4), key=lambda L: lane_busy_until[L])
        if chosen != wanted:
            n["lane"] = int(chosen)
        # Reserve
        if "dur" in n:
            lane_busy_until[chosen] = t + int(n["dur"]) + HOLD_TAIL_BUFFER_MS
        else:
            lane_busy_until[chosen] = t + MIN_SAME_LANE_GAP_MS
        recent_window.append((t, chosen))

    # Truncate hold tails that would still extend into a subsequent same-lane note
    by_lane: dict[int, list[dict]] = {0: [], 1: [], 2: [], 3: []}
    for n in out:
        by_lane[n["lane"]].append(n)
    for L, lane_notes in by_lane.items():
        for i in range(len(lane_notes) - 1):
            a, b = lane_notes[i], lane_notes[i + 1]
            if "dur" in a:
                max_end = b["t"] - HOLD_TAIL_BUFFER_MS
                if a["t"] + a["dur"] > max_end:
                    new_dur = max(0, max_end - a["t"])
                    if new_dur < HOLD_MIN_MS - 200:
                        del a["dur"]   # demote hold -> tap if it'd be too short
                    else:
                        a["dur"] = int(new_dur)

    out.sort(key=lambda n: (n["t"], n["lane"]))
    hold_count = sum(1 for n in out if "dur" in n)
    print(f"[info] FINAL {len(out)} notes (holds={hold_count}, BPM={tempo:.0f})", file=sys.stderr)
    return out


def emit_js(beatmap: list[dict]) -> str:
    rows = []
    for b in beatmap:
        if "dur" in b:
            rows.append(f"{{ t: {b['t']}, lane: {b['lane']}, dur: {b['dur']} }}")
        else:
            rows.append(f"{{ t: {b['t']}, lane: {b['lane']} }}")
    return "const beatMap = [\n    " + ",\n    ".join(rows) + "\n  ];"


if __name__ == "__main__":
    if not AUDIO.exists():
        sys.exit(f"missing audio: {AUDIO}")
    beatmap = analyse(AUDIO)
    OUT_JSON.write_text(json.dumps(beatmap, indent=2), encoding="utf-8")
    print(emit_js(beatmap))
    print(f"\n[ok] wrote {OUT_JSON.relative_to(ROOT)}", file=sys.stderr)
