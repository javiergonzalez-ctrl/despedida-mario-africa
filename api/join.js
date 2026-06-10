import { sql, bad } from './_db.js';

// POST {room, pid, name} — register (or rename) a phone player in the room.
export default async function handler(req, res) {
  if (req.method !== 'POST') return bad(res, 'POST only', 405);
  const { room, pid, name } = req.body || {};
  if (!room || !pid || !name) return bad(res, 'room, pid, name required');
  const cleanName = String(name).slice(0, 24);
  await sql`
    INSERT INTO asb_players (room, pid, name) VALUES (${room}, ${pid}, ${cleanName})
    ON CONFLICT (room, pid) DO UPDATE SET name = ${cleanName}`;
  res.status(200).json({ ok: true });
}
