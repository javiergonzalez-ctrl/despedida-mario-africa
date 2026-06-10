import { neon } from '@neondatabase/serverless';

// Shared Neon HTTP client. DATABASE_URL lives in Vercel env vars — never in code.
export const sql = neon(process.env.DATABASE_URL);

export function bad(res, msg, code = 400) {
  return res.status(code).json({ error: msg });
}
