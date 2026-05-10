// Centered modal containing the "Use this from code" panel. Opened from the
// "View as Python" link in Tab 1's input footer. Three-feature × three-language
// matrix: pick which feature's snippet to show (Manual / Notation / Audio),
// pick the language (py / cli / curl), copy to clipboard, dismiss via × /
// backdrop / Escape.
//
// Snippet content is the same shape the prototype shipped — keep them in sync
// with whatever lives in `/docs/` if those examples ever drift.

import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import Eyebrow from './ui/Eyebrow';

export type CodeModalTab = 'manual' | 'upload' | 'audio';
export type CodeModalLang = 'py' | 'cli' | 'curl';

interface CodeModalProps {
  open: boolean;
  initialTab?: CodeModalTab;
  initialLang?: CodeModalLang;
  onClose: () => void;
}

// Per-feature snippets. Bodies are intentionally compact — the modal isn't a
// tutorial, just a "here's the same call from your editor" pointer.
//
// `label` is the long-form name (used in the body eyebrow); `short` is the
// compact name that fits the toolbar pill without wrapping.
const CODE_TABS: Record<
  CodeModalTab,
  { label: string; short: string; summary: string; py: string; cli: string; curl: string }
> = {
  manual: {
    label: 'Manual entry',
    short: 'Manual',
    summary:
      'Hand a list of chord symbols to the engine. Optionally pin the key or the style profile, and turn on educational explanations.',
    py: `from harmonic_analysis.services import PatternAnalysisService

service = PatternAnalysisService()

result = await service.analyze_with_patterns_async(
    ['Dm', 'G7', 'Cmaj7'],
    key="C major",            # optional — None = auto-detect
    profile="classical",      # or "jazz", "pop", "modal", None
    include_educational=True,
)

print(result.primary.key_signature)     # → "C major"
print(result.primary.roman_numerals)    # → ['ii', 'V7', 'Imaj7']
print(result.primary.confidence)        # → 0.92`,
    cli: `# CLI equivalent
ha analyze "Dm G7 Cmaj7" --key "C major" --profile classical --educational`,
    curl: `curl -X POST http://localhost:8000/api/analyze \\
  -H "Content-Type: application/json" \\
  -d '{
    "chords": ["Dm", "G7", "Cmaj7"],
    "key": "C major",
    "profile": "classical",
    "include_educational": true
  }'`,
  },
  upload: {
    label: 'Analyze notation',
    short: 'Notation',
    summary:
      'Feed a MusicXML or MIDI file to the same engine. The library extracts the chord progression from the notation and runs the same multi-profile analysis as manual entry.',
    py: `from harmonic_analysis.services import (
    PatternAnalysisService,
    MusicFileProcessor,
)

processor = MusicFileProcessor()
extracted = processor.process_file("etude.musicxml")

# extracted.chord_symbols → ['Am', 'Dm', 'G', 'C', ...]
# extracted.key_hint      → "A minor"

service = PatternAnalysisService()
result  = await service.analyze_with_patterns_async(
    extracted.chord_symbols,
    key=extracted.key_hint,
    profile="classical",
)`,
    cli: `# CLI equivalent
ha analyze-file etude.musicxml --profile classical`,
    curl: `curl -X POST http://localhost:8000/api/analyze/file \\
  -F "file=@etude.musicxml" \\
  -F "profile=classical" \\
  -F "run_analysis=true"`,
  },
  audio: {
    label: 'Audio analysis',
    short: 'Audio',
    summary:
      'Run key detection + time-aligned chord estimation on a recording, then optionally hand the extracted chord labels back to the pattern engine for the full Roman-numeral reading.',
    py: `from harmonic_analysis.audio   import AudioAnalyzer
from harmonic_analysis.services import PatternAnalysisService

# 1. audio → time-aligned chords + key
audio = AudioAnalyzer()
audio_result = await audio.analyze_file("riff.wav")

# 2. (optional) feed the chord labels into pattern analysis
labels = [c.chord_label for c in audio_result.chord_progression]
service = PatternAnalysisService()
patterns = await service.analyze_with_patterns_async(
    labels,
    key=f"{audio_result.local.tonic} {audio_result.local.mode}",
    include_educational=True,
)`,
    cli: `# CLI equivalent
ha analyze-audio riff.wav --run-pattern-analysis`,
    curl: `curl -X POST http://localhost:8000/api/analyze/audio \\
  -F "file=@riff.wav" \\
  -F "run_pattern_analysis=true"`,
  },
};

// Token order matters: comments first so `#` lines don't get keyword-painted;
// strings next so quoted text isn't accidentally split on keyword regex; then
// keywords last on whatever remains. Each token type produces a span with its
// own color. Returns a list of React nodes — no raw HTML, no innerHTML.
const PY_KEYWORDS = new Set([
  'from', 'import', 'as', 'async', 'await', 'def', 'return', 'None', 'True',
  'False', 'in', 'for', 'if', 'else', 'elif', 'with', 'class', 'print',
]);

const IDENT_RE = /^[A-Za-z_][A-Za-z0-9_]*/;
const PLAIN_RE = /^[^"'#A-Za-z_]+/;

// Walk a single line, peeling off the leftmost match of comment / string /
// keyword / plain at each step. Cheap to implement, plenty fast for the size of
// snippet we're showing.
const tokenizePythonLine = (line: string): ReactNode[] => {
  const out: ReactNode[] = [];
  let i = 0;
  let key = 0;
  while (i < line.length) {
    // Comment to end of line
    if (line[i] === '#') {
      out.push(
        <span key={key++} className="text-slate-400 italic">
          {line.slice(i)}
        </span>,
      );
      break;
    }
    // String literal — single or double quoted, simple (no escape handling)
    if (line[i] === '"' || line[i] === "'") {
      const quote = line[i];
      const end = line.indexOf(quote, i + 1);
      const stop = end === -1 ? line.length : end + 1;
      out.push(
        <span key={key++} className="text-emerald-700">
          {line.slice(i, stop)}
        </span>,
      );
      i = stop;
      continue;
    }
    // Identifier / keyword (letters, digits, underscore)
    const remaining = line.slice(i);
    const ident = remaining.match(IDENT_RE);
    if (ident) {
      const word = ident[0];
      if (PY_KEYWORDS.has(word)) {
        out.push(
          <span key={key++} className="text-primary-700 font-semibold">
            {word}
          </span>,
        );
      } else {
        out.push(<Fragment key={key++}>{word}</Fragment>);
      }
      i += word.length;
      continue;
    }
    // Plain run — anything that isn't a quote, hash, or identifier-start
    const plain = remaining.match(PLAIN_RE);
    if (plain) {
      out.push(<Fragment key={key++}>{plain[0]}</Fragment>);
      i += plain[0].length;
      continue;
    }
    // Defensive: should be unreachable, but advance to avoid an infinite loop
    out.push(<Fragment key={key++}>{line[i]}</Fragment>);
    i += 1;
  }
  return out;
};

const PythonHighlight = ({ src }: { src: string }) => {
  const lines = src.split('\n');
  return (
    <>
      {lines.map((line, idx) => (
        <Fragment key={idx}>
          {tokenizePythonLine(line)}
          {idx < lines.length - 1 ? '\n' : ''}
        </Fragment>
      ))}
    </>
  );
};

// Inline </> glyph — matches the eighth-note family used in Header.tsx.
const CodeIcon = ({ className = 'w-4 h-4' }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);

const CopyIcon = ({ className = 'w-3.5 h-3.5' }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);

const CodeModal = ({ open, initialTab = 'manual', initialLang = 'py', onClose }: CodeModalProps) => {
  const [tab, setTab] = useState<CodeModalTab>(initialTab);
  const [lang, setLang] = useState<CodeModalLang>(initialLang);
  const [copied, setCopied] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Resync when reopened with a different default — avoids the modal showing
  // stale tab state from the previous open.
  useEffect(() => {
    if (open) {
      setTab(initialTab);
      setLang(initialLang);
      setCopied(false);
    }
  }, [open, initialTab, initialLang]);

  // Escape dismisses; mounting/unmounting the listener with `open` so closed
  // modals don't poison the global keymap.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // Lock body scroll while the modal is up — otherwise the page behind the
  // backdrop can still scroll under the user's pointer.
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  const current = CODE_TABS[tab];
  const src = useMemo(() => {
    if (lang === 'py') return current.py;
    if (lang === 'cli') return current.cli;
    return current.curl;
  }, [current, lang]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(src);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      // Some browsers refuse clipboard in insecure contexts. Silent fail is
      // better than throwing — the snippet is still selectable.
    }
  }, [src]);

  if (!open) return null;

  const tabs: CodeModalTab[] = ['manual', 'upload', 'audio'];
  const langs: CodeModalLang[] = ['py', 'cli', 'curl'];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="code-modal-title"
    >
      {/* Backdrop — click to dismiss. */}
      <button
        type="button"
        onClick={onClose}
        aria-label="Close code panel"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm cursor-default"
      />

      <div
        ref={dialogRef}
        className="relative z-10 w-[680px] max-w-[92vw] max-h-[85vh] rounded-2xl border border-slate-200 bg-white shadow-[0_-8px_32px_rgba(15,23,42,0.10),0_-2px_8px_rgba(15,23,42,0.04)] overflow-hidden flex flex-col"
      >
        {/* Toolbar — flex-wrap so cramped viewports stack the title above the
            controls instead of truncating. Short tab labels (Manual / Notation
            / Audio) keep the pill compact; the long label still shows as the
            body eyebrow so context isn't lost. */}
        <div className="flex items-center justify-between gap-x-3 gap-y-2 flex-wrap px-5 py-3 border-b border-slate-200 bg-slate-50/60 flex-shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <CodeIcon className="w-4 h-4 text-primary-700 flex-shrink-0" />
            <span
              id="code-modal-title"
              className="font-serif text-lg font-semibold text-slate-900 leading-none whitespace-nowrap"
            >
              Use this from code
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Feature tab toggle */}
            <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-md p-0.5">
              {tabs.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`text-xs px-2 py-1 rounded transition whitespace-nowrap ${
                    tab === t
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {CODE_TABS[t].short}
                </button>
              ))}
            </div>
            {/* Language toggle */}
            <div className="flex items-center gap-1 text-[11px] font-mono">
              {langs.map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => setLang(l)}
                  className={`px-1.5 py-0.5 rounded uppercase tracking-wider border ${
                    lang === l
                      ? 'bg-primary-50 text-primary-800 border-primary-200'
                      : 'text-slate-500 hover:text-slate-800 border-transparent'
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-medium py-1 px-2 rounded-lg text-xs transition"
            >
              <CopyIcon />
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="w-7 h-7 grid place-items-center rounded-md hover:bg-slate-200 text-slate-500"
            >
              ×
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-3 overflow-y-auto">
          <Eyebrow tone="primary">{current.label}</Eyebrow>
          <p className="text-sm text-slate-600 leading-relaxed">{current.summary}</p>
          <pre
            className="text-[12px] leading-[1.65] font-mono text-slate-800 bg-slate-50 px-4 py-3 rounded-lg overflow-x-auto border border-slate-200"
            aria-label={`${lang} sample`}
          >
            <code>{lang === 'py' ? <PythonHighlight src={src} /> : src}</code>
          </pre>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
            <a
              href="https://github.com/sammywachtel/harmonic-analysis/blob/main/docs/README.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-700 hover:underline"
            >
              Full API reference →
            </a>
            <a
              href="https://pypi.org/project/harmonic-analysis/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-600 hover:underline"
            >
              Install on PyPI →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeModal;
