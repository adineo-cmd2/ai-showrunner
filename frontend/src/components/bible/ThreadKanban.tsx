import { useEffect, useState } from 'react';
import { apiGet, apiPatch } from '../../lib/apiClient';

interface Thread {
  id: number;
  title: string;
  status: string;
  last_seen: number;
}

interface ThreadsData {
  active: Thread[];
  dormant: Thread[];
  resolved: Thread[];
}

const COLUMNS: Array<{ key: keyof ThreadsData; label: string }> = [
  { key: 'active', label: 'Active' },
  { key: 'dormant', label: 'Dormant' },
  { key: 'resolved', label: 'Resolved' },
];

export default function ThreadKanban({ storyId }: { storyId: string }) {
  const [data, setData] = useState<ThreadsData | null>(null);
  const [error, setError] = useState('');
  const [resolving, setResolving] = useState<number | null>(null);

  useEffect(() => {
    if (!storyId) return;
    apiGet(`/api/story/${storyId}/threads`)
      .then((t) => setData(t as ThreadsData))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load threads.'));
  }, [storyId]);

  async function resolve(t: Thread) {
    setResolving(t.id);
    try {
      await apiPatch(`/api/story/threads/${t.id}`, { status: 'resolved' });
      setData((d) => {
        if (!d) return d;
        const without = {
          active: d.active.filter((x) => x.id !== t.id),
          dormant: d.dormant.filter((x) => x.id !== t.id),
          resolved: d.resolved.filter((x) => x.id !== t.id),
        };
        return { ...without, resolved: [...without.resolved, { ...t, status: 'resolved' }] };
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Resolve failed.');
    } finally {
      setResolving(null);
    }
  }

  if (!storyId) return <p className="text-sm text-stone-400">No story selected.</p>;
  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!data) return <p className="text-sm text-stone-400">Loading threads…</p>;

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {COLUMNS.map((col) => (
        <section key={col.key} className="border border-charcoal-line bg-charcoal p-3">
          <h3 className="mono-n text-xs uppercase tracking-widest text-brand">
            {col.label} ({data[col.key].length})
          </h3>
          <div className="mt-2 space-y-2">
            {data[col.key].map((t) => (
              <article key={t.id} className="border border-charcoal-line bg-ink p-3">
                <p className="text-sm font-bold text-stone-100">{t.title}</p>
                <p className="mono-n mt-1 text-xs text-stone-500">last seen ep {t.last_seen}</p>
                {t.status !== 'resolved' && (
                  <button
                    className="mt-2 text-xs underline text-brand disabled:opacity-50"
                    disabled={resolving === t.id}
                    onClick={() => resolve(t)}
                  >
                    {resolving === t.id ? 'Resolving…' : 'Resolve'}
                  </button>
                )}
              </article>
            ))}
            {data[col.key].length === 0 && (
              <p className="text-sm text-stone-500">Nothing here.</p>
            )}
          </div>
        </section>
      ))}
    </div>
  );
}
