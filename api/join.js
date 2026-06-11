import { sql, bad } from './_db.js';

// POST {room, pid, name} — register (or rename) a phone player in the room.
// Identidad por NOMBRE: si ya existe un jugador con ese nombre en la sala
// (mismo amigo desde incógnito / otro móvil / otra sesión), devolvemos SU pid
// para que el cliente lo adopte — nada de jugadores duplicados, y conserva
// sus chupitos. Dos personas reales con el mismo nombre compartirán ficha:
// que se pongan motes.
export default async function handler(req, res) {
  if (req.method !== 'POST') return bad(res, 'POST only', 405);
  const { room, pid, name } = req.body || {};
  if (!room || !pid || !name) return bad(res, 'room, pid, name required');
  const cleanName = String(name).slice(0, 24);
  const [existing] = await sql`
    SELECT pid FROM asb_players WHERE room = ${room} AND lower(name) = lower(${cleanName}) LIMIT 1`;
  if (existing && existing.pid !== pid) {
    return res.status(200).json({ ok: true, pid: existing.pid, merged: true });
  }
  await sql`
    INSERT INTO asb_players (room, pid, name) VALUES (${room}, ${pid}, ${cleanName})
    ON CONFLICT (room, pid) DO UPDATE SET name = ${cleanName}`;
  res.status(200).json({ ok: true, pid });
}
