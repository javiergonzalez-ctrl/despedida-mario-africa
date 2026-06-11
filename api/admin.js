import { sql, bad } from './_db.js';

// POST — herramientas del anfitrión (página ?admin=1):
//  {action:'kick', room, pid}          echar a un jugador (y sus votos)
//  {action:'reset-votes', room, round} borrar los votos de una ronda y reabrirla
//  {action:'reset-room', room}         vaciar la sala entera (jugadores+rondas+votos)
// Barrera de seguridad consciente: conocer el room id. Es una herramienta de
// fiesta entre amigos; no hay auth real. No exponer rooms públicamente.
export default async function handler(req, res) {
  if (req.method !== 'POST') return bad(res, 'POST only', 405);
  const { action, room, pid, round } = req.body || {};
  if (!room || !action) return bad(res, 'room, action required');

  if (action === 'kick') {
    if (!pid) return bad(res, 'pid required');
    await sql`DELETE FROM asb_predictions WHERE room = ${room} AND pid = ${pid}`;
    await sql`DELETE FROM asb_players WHERE room = ${room} AND pid = ${pid}`;
    return res.status(200).json({ ok: true });
  }
  if (action === 'reset-votes') {
    if (round === undefined) return bad(res, 'round required');
    await sql`DELETE FROM asb_predictions WHERE room = ${room} AND round = ${round}`;
    await sql`UPDATE asb_rounds SET state = 'open' WHERE room = ${room} AND round = ${round}`;
    return res.status(200).json({ ok: true });
  }
  if (action === 'reset-room') {
    await sql`DELETE FROM asb_predictions WHERE room = ${room}`;
    await sql`DELETE FROM asb_rounds WHERE room = ${room}`;
    await sql`DELETE FROM asb_players WHERE room = ${room}`;
    return res.status(200).json({ ok: true });
  }
  return bad(res, 'unknown action');
}
