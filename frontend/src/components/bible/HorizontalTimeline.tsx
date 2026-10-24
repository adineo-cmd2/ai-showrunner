import { useEffect, useState } from 'react';
import { apiGet } from '../../lib/apiClient';

interface TimelineEvent {
  id: number;
  episode_no: number;
  label: string;
  detail?: string;
}

export default function HorizontalTimeline({ storyId }: { storyId: string }) {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!storyId) return;
    apiGet(`/api/story/bible/${storyId}/full`)
      .then((b) => {
        const evs = ((b as { events: TimelineEvent[] }).events ?? []).slice();
        evs.sort((a, c) => a.episode_no - c.episode_no || a.id - c.id);
        setEvents(evs);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load timeline.'));
  }, [storyId]);

  if (!storyId) return <p className="text-sm text-stone-400">No story selected.</p>;
  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!events) return <p className="text-sm text-stone-400">Loading timeline…</p>;
  if (events.length === 0) return <p className="text-sm text-stone-400">No timeline events yet.</p>;

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {events.map((e) => (
        <article key={e.id} className="min-w-[220px] max-w-[220px] border border-charcoal-line bg-charcoal p-4">
          <p className="mono-n text-xs text-brand">EP {e.episode_no}</p>
          <p className="display-f mt-1 font-bold text-stone-100">{e.label || '(untitled beat)'}</p>
          {e.detail && <p className="mt-2 text-sm text-stone-400">{e.detail}</p>}
        </article>
      ))}
    </div>
  );
}
