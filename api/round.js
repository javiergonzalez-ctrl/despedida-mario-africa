import { sql, bad } from './_db.js';

// POST — round lifecycle + group punishments:
//  {action:'open', room, round, gameName}   start betting for a round
//  {action:'close', room, round}            stop accepting votes
//  {action:'group-shots', room, n}          assign n shots to random players
export default async function handler(req, res) {
  if (req.method !== 'POST') return bad(res, 'POST only', 405);
  const { action, room, round, gameName, n } = req.body || {};
  if (!room || !action) return bad(res, 'room, action required');

  if (action === 'open') {
    await sql`
      INSERT INTO asb_rounds (room, round, state, game_name) VALUES (${room}, ${round}, 'open', ${gameName || ''})
      ON CONFLICT (room, round) DO UPDATE SET state = 'open', game_name = ${gameName || ''}`;
    return res.status(200).json({ ok: true });
  }
  if (action === 'close') {
    await sql`UPDATE asb_rounds SET state = 'closed' WHERE room = ${room} AND round = ${round}`;
    return res.status(200).json({ ok: true });
  }
  if (action === 'group-shots') {
    const players = await sql`SELECT pid, name, chupitos FROM asb_players WHERE room = ${room}`;
    if (players.length === 0) return res.status(200).json({ ok: true, picks: [] });
    const shots = Math.max(1, Math.min(20, parseInt(n) || 1));
    for (let i = 0; i < shots; i++) {
      const p = players[Math.floor(Math.random() * players.length)];
      p.chupitos++;
      await sql`UPDATE asb_players SET chupitos = chupitos + 1 WHERE room = ${room} AND pid = ${p.pid}`;
    }
    return res.status(200).json({ ok: true, picks: players.map(p => ({ name: p.name, total: p.chupitos })) });
  }
  return bad(res, 'unknown action');
}
