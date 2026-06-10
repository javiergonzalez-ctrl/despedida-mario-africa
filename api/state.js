import { sql, bad } from './_db.js';

// GET ?room=X[&round=N][&pid=P] — single polling endpoint for TV and phones:
// players + per-round SI/NO counts + active round info (+ this phone's vote).
export default async function handler(req, res) {
  const { room, round, pid } = req.query || {};
  if (!room) return bad(res, 'room required');
  const players = await sql`
    SELECT pid, name, chupitos FROM asb_players WHERE room = ${room} ORDER BY chupitos DESC, name`;
  const [active] = await sql`
    SELECT round, state, game_name, last_result FROM asb_rounds
    WHERE room = ${room} ORDER BY round DESC LIMIT 1`;
  let counts = { si: 0, no: 0 };
  let myVote = null;
  const roundN = round !== undefined ? parseInt(round) : (active ? active.round : null);
  if (roundN !== null && !isNaN(roundN)) {
    const rows = await sql`
      SELECT choice, count(*)::int AS c FROM asb_predictions
      WHERE room = ${room} AND round = ${roundN} GROUP BY choice`;
    for (const r of rows) { if (r.choice === 1) counts.si = r.c; else counts.no = r.c; }
    if (pid) {
      const [mine] = await sql`
        SELECT choice, amount FROM asb_predictions
        WHERE room = ${room} AND round = ${roundN} AND pid = ${pid}`;
      if (mine) myVote = { choice: mine.choice, amount: mine.amount };
    }
  }
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ players, counts, activeRound: active || null, myVote });
}
