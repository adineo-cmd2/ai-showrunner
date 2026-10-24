import { useEffect, useRef, useState } from 'react';
import { apiPost } from '../../lib/apiClient';

interface LiveIssue {
  severity: string;
  kind: string;
  detail: string;
  passage?: string;
}

interface SubmitReport {
  episode_id: number;
  issues: LiveIssue[];
  pending: Array<{ id: number; action: string; payload: unknown; status: string }>;
  guns: Array<{ entity: string; detail?: string } | string>;
}

interface Suggestions {
  payoff?: string;
  beat?: string;
  world?: string;
}

function gunLabel(g: { entity: string; detail?: string } | string): string {
  if (typeof g === 'string') return g;
  return g.detail ? `${g.entity} — ${g.detail}` : g.entity;
}

export default function EpisodeEditor({ initialStoryId }: { initialStoryId: string }) {
  const [storyId, setStoryId] = useState(initialStoryId);
  const [number, setNumber] = useState('1');
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [warnings, setWarnings] = useState<LiveIssue[] | null>(null);
  const [ruleHits, setRuleHits] = useState<Array<{ rule: string }> | null>(null);
  const [checking, setChecking] = useState(false);
  const [report, setReport] = useState<SubmitReport | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestions | null>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const timer = useRef<number | null>(null);

  // Debounced 1s live consistency check. window only touched inside useEffect.
  useEffect(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
    if (!storyId || text.trim().length < 20) {
      setWarnings(null);
      setRuleHits(null);
      return;
    }
    setChecking(true);
    timer.current = window.setTimeout(() => {
      apiPost(`/api/story/${storyId}/episode/check`, { text })
        .then((r) => {
          setWarnings((r as { issues: LiveIssue[] }).issues ?? []);
          setRuleHits((r as { rule_hits: Array<{ rule: string }> }).rule_hits ?? []);
        })
        .catch(() => {
          // Live check is best-effort; submit surfaces real errors.
        })
        .finally(() => setChecking(false));
    }, 1000);
    return () => {
      if (timer.current !== null) {
        window.clearTimeout(timer.current);
        timer.current = null;
      }
    };
  }, [text, storyId]);

  async function submit() {
    setError('');
    setReport(null);
    setSuggestions(null);
    if (!storyId) {
      setError('Enter a story id first.');
      return;
    }
    const num = parseInt(number, 10);
    if (!Number.isFinite(num) || num < 1) {
      setError('Episode number must be a positive integer.');
      return;
    }
    if (text.trim().length === 0) {
      setError('Episode text is empty.');
      return;
    }
    setSubmitting(true);
    try {
      const r = (await apiPost(`/api/story/${storyId}/episode`, {
        number: num,
        title,
        text,
      })) as SubmitReport;
      setReport(r);
      try {
        const s = (await apiPost(`/api/story/${storyId}/suggest`, {})) as Suggestions;
        setSuggestions(s);
      } catch {
        // Suggestions are a bonus; the episode report stands alone.
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="block text-sm">
          <span className="mono-n text-xs text-stone-400">Story id</span>
          <input
            className="mt-1 w-full border border-charcoal-line bg-charcoal px-2 py-1 text-stone-100"
            value={storyId}
            onChange={(e) => setStoryId(e.target.value.trim())}
            placeholder="e.g. 1"
          />
        </label>
        <label className="block text-sm">
          <span className="mono-n text-xs text-stone-400">Episode number</span>
          <input
            className="mt-1 w-full border border-charcoal-line bg-charcoal px-2 py-1 text-stone-100"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            inputMode="numeric"
          />
        </label>
        <label className="block text-sm">
          <span className="mono-n text-xs text-stone-400">Episode title</span>
          <input
            className="mt-1 w-full border border-charcoal-line bg-charcoal px-2 py-1 text-stone-100"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="The Long Night"
          />
        </label>
      </div>
      <label className="mt-4 block text-sm">
        <span className="mono-n text-xs text-stone-400">Episode text</span>
        <textarea
          className="mono-n mt-1 min-h-[280px] w-full border border-charcoal-line bg-charcoal p-3 text-sm text-stone-100"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Write the episode in plain prose…"
        />
      </label>

      <div className="mt-3 border border-charcoal-line bg-charcoal p-4">
        <h3 className="mono-n text-xs uppercase tracking-widest text-brand">
          Consistency warnings {checking ? '(checking…)' : '(live)'}
        </h3>
        {warnings === null && (
          <p className="mt-2 text-sm text-stone-500">Type at least a sentence — live check runs 1s after you pause.</p>
        )}
        {warnings !== null && warnings.length === 0 && (
          <p className="mt-2 text-sm text-stone-300">No issues detected in the current draft.</p>
        )}
        {warnings !== null && warnings.length > 0 && (
          <ul className="mt-2 space-y-2">
            {warnings.map((w, i) => (
              <li key={i} className="text-sm text-stone-200">
                <span className="mono-n mr-2 border border-brand px-1 text-xs text-brand">{w.severity}</span>
                {w.detail}
              </li>
            ))}
          </ul>
        )}
        {ruleHits !== null && ruleHits.length > 0 && (
          <p className="mono-n mt-2 text-xs text-stone-500">
            rule hits: {ruleHits.map((h) => h.rule).join(' · ')}
          </p>
        )}
      </div>

      <button
        className="mt-4 border border-brand px-4 py-2 text-sm font-bold text-brand hover:bg-brand hover:text-ink disabled:opacity-50"
        disabled={submitting}
        onClick={submit}
      >
        {submitting ? 'Submitting…' : 'Submit episode'}
      </button>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

      {report && (
        <div className="mt-4 border border-charcoal-line bg-charcoal p-4">
          <h3 className="display-f text-lg text-stone-100">Episode report #{report.episode_id}</h3>
          <h4 className="mono-n mt-3 text-xs uppercase tracking-widest text-brand">
            Issues ({report.issues.length})
          </h4>
          {report.issues.length === 0 && <p className="mt-1 text-sm text-stone-300">Clean — no continuity issues.</p>}
          <ul className="mt-1 space-y-1">
            {report.issues.map((w, i) => (
              <li key={i} className="text-sm text-stone-200">
                <span className="mono-n mr-2 border border-brand px-1 text-xs text-brand">{w.severity}</span>
                {w.detail}
              </li>
            ))}
          </ul>
          <h4 className="mono-n mt-3 text-xs uppercase tracking-widest text-brand">
            Pending bible changes ({report.pending.length})
          </h4>
          {report.pending.length === 0 && <p className="mt-1 text-sm text-stone-300">Nothing awaiting confirmation.</p>}
          <ul className="mt-1 space-y-1">
            {report.pending.map((p) => (
              <li key={p.id} className="mono-n text-xs text-stone-300">
                #{p.id} {p.action} — confirm in the Bible tab
              </li>
            ))}
          </ul>
          <h4 className="mono-n mt-3 text-xs uppercase tracking-widest text-brand">
            Chekhov guns ({report.guns.length})
          </h4>
          {report.guns.length === 0 && <p className="mt-1 text-sm text-stone-300">No open guns.</p>}
          <ul className="mt-1 space-y-1">
            {report.guns.map((g, i) => (
              <li key={i} className="text-sm text-stone-200">{gunLabel(g)}</li>
            ))}
          </ul>
          {suggestions && (
            <>
              <h4 className="mono-n mt-3 text-xs uppercase tracking-widest text-brand">Suggestions</h4>
              <ul className="mt-1 space-y-1 text-sm text-stone-200">
                {suggestions.payoff && <li><span className="font-bold">Payoff: </span>{suggestions.payoff}</li>}
                {suggestions.beat && <li><span className="font-bold">Beat: </span>{suggestions.beat}</li>}
                {suggestions.world && <li><span className="font-bold">World: </span>{suggestions.world}</li>}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
