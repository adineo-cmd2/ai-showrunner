// Centralised fetch for the AI Showrunner backend (no auth, single local user).
// Backend defaults to http://localhost:8005; override with PUBLIC_API_BASE.

export const BASE: string =
  (import.meta.env.PUBLIC_API_BASE as string | undefined) ??
  'http://localhost:8005';

async function handle(res: Response): Promise<any> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = (data as { detail?: string }).detail ?? JSON.stringify(data);
    } catch {
      // keep statusText
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json();
}

export async function apiGet(path: string): Promise<any> {
  const res = await fetch(`${BASE}${path}`);
  return handle(res);
}

export async function apiPost(path: string, body: unknown): Promise<any> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handle(res);
}

// Alias kept for parity with sibling frontends.
export const apiPostJSON = apiPost;

export async function apiPatch(path: string, body?: unknown): Promise<any> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return handle(res);
}

export async function apiDelete(path: string): Promise<any> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'DELETE',
  });
  return handle(res);
}
