import { useEffect, useState } from 'react';
import { apiGet } from '../../lib/apiClient';

interface Issue {
  id: number;
  severity: string;
  kind: string;
  detail: string;
  passage?: string;
  episode_id: number;
  episode_no: number;
}

const FILTERS = ['ALL', 'CRITICAL', 'WARNING', 'MINOR'] as const;

export default function IssueTable({ storyId }: { storyId: string }) {
  const [issues, setIssues] = useState<Issue[] | null>(null);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('ALL');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!storyId) return;
    apiGet(`/api/story/${storyId}/continuity`)
      .then((c) => setIssues((c as { issues: Issue[] }).issues ?? []))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load continuity.'));
  }, [storyId]);

  if (!storyId) return <p className="text-sm text-stone-400">No story selected.</p>;
  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!issues) return <p className="text-sm text-stone-400">Loading continuity…</p>;

  const visible = filter === 'ALL' ? issues : issues.filter((i) => i.severity === filter);

  function sevClass(sev: string): string {
    if (sev === 'CRITICAL') return 'border-red-500 text-red-400';
    if (sev === 'WARNING') return 'border-brand text-brand';
    return 'border-stone-500 text-stone-400';
  }

  return (
    <div>
      <label className="mono-n text-xs text-stone-400" htmlFor="sev-filter">
        Severity filter
      </label>
      <select
        id="sev-filter"
        className="mono-n ml-2 border border-charcoal-line bg-charcoal px-2 py-1 text-xs text-stone-200"
        value={filter}
        onChange={(e) => setFilter(e.target.value as (typeof FILTERS)[number])}
      >
        {FILTERS.map((f) => (
          <option key={f} value={f}>
            {f}
          </option>
        ))}
      </select>
      <div className="mt-4 space-y-2">
        {visible.map((i) => (
          <article key={i.id} className="border border-charcoal-line bg-charcoal p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`mono-n border px-1 text-xs ${sevClass(i.severity)}`}>{i.severity}</span>
              <span className="mono-n text-xs text-stone-500">{i.kind}</span>
              <a
                className="mono-n text-xs text-brand underline"
                href={`/episode-editor?story=${encodeURIComponent(storyId)}`}
              >
                Ep {i.episode_no}
              </a>
            </div>
            <p className="mt-2 text-sm text-stone-200">{i.detail}</p>
            {i.passage && (
              <blockquote className="mt-1 border-l-2 border-charcoal-line pl-2 text-sm italic text-stone-400">
                “{i.passage}”
              </blockquote>
            )}
          </article>
        ))}
        {visible.length === 0 && <p className="text-sm text-stone-500">No issues at this severity.</p>}
      </div>
    </div>
  );
}
