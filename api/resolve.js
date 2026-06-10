import { sql, bad } from './_db.js';

// POST {room, round, passed} — settle a round: losers (wrong side) drink
// baseShots × their wager. Returns the drinkers ranking for the TV.
export default async function handler(req, res) {
  if (req.method !== 'POST') return bad(res, 'POST only', 405);
  const { room, round, passed } = req.body || {};
  if (!room || round === undefined || passed === undefined) return bad(res, 'room, round, passed required');

  const preds = await sql`
    SELECT p.pid, p.choice, p.amount, pl.name, pl.chupitos
    FROM asb_predictions p
    JOIN asb_players pl ON pl.room = p.room AND pl.pid = p.pid
    WHERE p.room = ${room} AND p.round = ${round}`;
  const loserSide = passed ? 0 : 1;
  const baseShotsEach = passed ? 1 : 2;
  let si = 0, no = 0;
  const losers = [];
  for (const p of preds) {
    if (p.choice === 1) si++; else no++;
    if (p.choice === loserSide) {
      const shotsForThis = baseShotsEach * Math.max(1, Math.min(10, p.amount));
      const newTotal = p.chupitos + shotsForThis;
      await sql`UPDATE asb_players SET chupitos = ${newTotal} WHERE room = ${room} AND pid = ${p.pid}`;
      losers.push({ name: p.name, shots: shotsForThis, total: newTotal, bet: p.amount });
    }
  }
  const lastResult = `Mario ${passed ? '✅ PASÓ' : '❌ FALLÓ'}`;
  await sql`
    INSERT INTO asb_rounds (room, round, state, last_result) VALUES (${room}, ${round}, 'result', ${lastResult})
    ON CONFLICT (room, round) DO UPDATE SET state = 'result', last_result = ${lastResult}`;
  res.status(200).json({ losers, si, no, passed, shotsEach: baseShotsEach });
}
