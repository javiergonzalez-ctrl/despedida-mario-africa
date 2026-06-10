import { sql, bad } from './_db.js';

// POST {room, round, pid, choice, amount} — cast/replace a prediction.
// choice: 0|1 for SÍ/NO prediction rounds (1 = SÍ, 0 = NO),
//         0..3 for A/B/C/D audience-lifeline rounds (round id 800-899).
// amount: 1-10 shots wagered (ignored by lifeline rounds).
export default async function handler(req, res) {
  if (req.method !== 'POST') return bad(res, 'POST only', 405);
  const { room, round, pid, choice, amount } = req.body || {};
  if (!room || round === undefined || !pid || ![0, 1, 2, 3].includes(choice)) {
    return bad(res, 'room, round, pid, choice(0..3) required');
  }
  const amt = Math.max(1, Math.min(10, parseInt(amount) || 1));
  const [r] = await sql`SELECT state FROM asb_rounds WHERE room = ${room} AND round = ${round}`;
  if (r && r.state !== 'open') return bad(res, 'round closed', 409);
  await sql`
    INSERT INTO asb_predictions (room, round, pid, choice, amount)
    VALUES (${room}, ${round}, ${pid}, ${choice}, ${amt})
    ON CONFLICT (room, round, pid) DO UPDATE SET choice = ${choice}, amount = ${amt}`;
  res.status(200).json({ ok: true });
}
