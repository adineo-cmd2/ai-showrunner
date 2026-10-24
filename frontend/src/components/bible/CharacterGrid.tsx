import { useEffect, useState } from 'react';
import { apiGet } from '../../lib/apiClient';

interface Character {
  id: number;
  name: string;
  traits?: string;
  backstory?: string;
  status?: string;
  arc?: string;
}

export default function CharacterGrid({ storyId }: { storyId: string }) {
  const [chars, setChars] = useState<Character[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!storyId) return;
    apiGet(`/api/story/bible/${storyId}/full`)
      .then((b) => setChars((b as { characters: Character[] }).characters ?? []))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load characters.'));
  }, [storyId]);

  if (!storyId) return <p className="text-sm text-stone-400">No story selected.</p>;
  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!chars) return <p className="text-sm text-stone-400">Loading characters…</p>;
  if (chars.length === 0) return <p className="text-sm text-stone-400">No characters yet. Add them from the episode pipeline or POST /api/story/{'{id}'}/characters.</p>;

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {chars.map((c) => (
        <article key={c.id} className="border border-charcoal-line bg-charcoal p-4">
          <div className="flex items-center justify-between">
            <p className="display-f font-bold text-stone-100">{c.name}</p>
            <span
              className={`mono-n border px-1 text-xs ${
                c.status === 'dead' ? 'border-red-500 text-red-400' : 'border-brand text-brand'
              }`}
            >
              {c.status || 'alive'}
            </span>
          </div>
          {c.traits && <p className="mt-2 text-sm text-stone-300">{c.traits}</p>}
          {c.backstory && <p className="mt-1 text-sm text-stone-400">{c.backstory}</p>}
          {c.arc && <p className="mono-n mt-2 text-xs text-stone-500">arc: {c.arc}</p>}
        </article>
      ))}
    </div>
  );
}
