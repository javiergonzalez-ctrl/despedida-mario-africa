"""
Generate a beatMap for the rhythm mini-game from cara-al-sol.mp3.

Guitar Hero-style: follow the REAL accents of the song, irregular gaps OK.

Approach:
  1. Load the MP3 mono at 22050 Hz.
  2. Run onset_detect with a permissive delta so we catch every real accent.
  3. Sort by time (NOT by strength — we keep the song's natural rhythm).
  4. Apply only a small min-gap (180ms) so consecutive notes are tappable.
  5. If there are still more notes than MAX_NOTES, drop the WEAKEST ones
     (not the latest), preserving the original time order.
  6. Assign lanes from the spectral centroid at each onset, so high-pitched
     accents go to the right lanes and low-pitched ones to the left.

Run:  python scripts/analyze_rhythm.py
Out:  scripts/beatmap.json + a JS literal printed to stdout.
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

MAX_NOTES = 30              # ceiling; weakest dropped first
MIN_GAP_MS = 220            # tappable minimum spacing
START_AT_MS = 1500          # ignore intro silence / count-in
STOP_AT_MS = 50_000         # only chart the first 50s (first verse + chorus)
END_BEFORE_MS = 1500        # leave tail clear (used if STOP_AT_MS=None)
ONSET_DELTA = 0.07          # how sensitive onset detection is (low = more notes)


def analyse(audio_path: Path) -> list[dict]:
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    duration_ms = int(librosa.get_duration(y=y, sr=sr) * 1000)
    print(f"[info] loaded {audio_path.name} -- {duration_ms/1000:.1f}s, sr={sr}", file=sys.stderr)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr,
        units="frames",
        backtrack=False,
        delta=ONSET_DELTA,
        wait=2,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    onset_strengths = onset_env[onset_frames]
    print(f"[info] {len(onset_frames)} raw onsets detected (delta={ONSET_DELTA})", file=sys.stderr)

    # Spectral centroid per frame for lane assignment
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    cent_at_onset = centroid[np.clip(onset_frames, 0, len(centroid) - 1)]

    # Step 1: filter by time window + enforce MIN_GAP_MS in time order
    end_ms = STOP_AT_MS if STOP_AT_MS is not None else (duration_ms - END_BEFORE_MS)
    onsets_in_window = []  # (t_ms, strength, centroid)
    last_ms = -10_000
    for t_s, strength, cent in zip(onset_times, onset_strengths, cent_at_onset):
        ms = int(t_s * 1000)
        if ms < START_AT_MS or ms > end_ms:
            continue
        if ms - last_ms < MIN_GAP_MS:
            # If this onset is much stronger than the previous kept one, replace it
            if onsets_in_window and strength > onsets_in_window[-1][1] * 1.5:
                onsets_in_window[-1] = (ms, float(strength), float(cent))
                last_ms = ms
            continue
        onsets_in_window.append((ms, float(strength), float(cent)))
        last_ms = ms

    print(f"[info] {len(onsets_in_window)} onsets after time-window + min-gap", file=sys.stderr)

    # Step 2: if still too many, drop the WEAKEST ones (keeps natural rhythm)
    if len(onsets_in_window) > MAX_NOTES:
        # Mark indices to drop: weakest first
        ranked = sorted(range(len(onsets_in_window)), key=lambda i: onsets_in_window[i][1])
        drop = set(ranked[: len(onsets_in_window) - MAX_NOTES])
        onsets_in_window = [o for i, o in enumerate(onsets_in_window) if i not in drop]
        print(f"[info] dropped {len(drop)} weakest -> {len(onsets_in_window)} kept", file=sys.stderr)

    if not onsets_in_window:
        return []

    # Step 3: lane assignment from centroid (normalised across kept set)
    cents = np.array([c for _, _s, c in onsets_in_window])
    if cents.max() == cents.min():
        lane_norm = np.zeros_like(cents)
    else:
        lane_norm = (cents - cents.min()) / (cents.max() - cents.min())
    lanes = np.clip((lane_norm * 4).astype(int), 0, 3)

    # Anti-repeat: no more than 2 consecutive notes in the same lane
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

    beatmap = [{"t": int(ms), "lane": int(l)} for (ms, _s, _c), l in zip(onsets_in_window, lanes)]

    if len(beatmap) >= 2:
        gaps = [beatmap[i+1]["t"] - beatmap[i]["t"] for i in range(len(beatmap)-1)]
        print(
            f"[info] first={beatmap[0]['t']}ms last={beatmap[-1]['t']}ms "
            f"notes={len(beatmap)} "
            f"avg-gap={sum(gaps)/len(gaps):.0f}ms "
            f"min-gap={min(gaps)}ms max-gap={max(gaps)}ms",
            file=sys.stderr,
        )
    return beatmap


def emit_js(beatmap: list[dict]) -> str:
    rows = ",\n    ".join(f"{{ t: {b['t']}, lane: {b['lane']} }}" for b in beatmap)
    return f"const beatMap = [\n    {rows}\n  ];"


if __name__ == "__main__":
    if not AUDIO.exists():
        sys.exit(f"missing audio: {AUDIO}")
    beatmap = analyse(AUDIO)
    OUT_JSON.write_text(json.dumps(beatmap, indent=2), encoding="utf-8")
    print(emit_js(beatmap))
    print(f"\n[ok] wrote {OUT_JSON.relative_to(ROOT)}", file=sys.stderr)
