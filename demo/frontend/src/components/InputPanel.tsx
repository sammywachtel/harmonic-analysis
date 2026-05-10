// Left column of the Tab 1 workbench. Three vertical regions:
//
//   1. Title strip      — eyebrow + serif H1 + helper line
//   2. Form body        — chord textarea, quick-example chips, key + profile
//                         selects, educational notes checkbox (scrollable for
//                         very short viewports)
//   3. Action footer    — primary Analyze button + "View as Python" link
//
// State and behavior live up in Tab1.tsx — this is a presentational shell.
// Everything the user can change is passed in as a value + onChange pair so
// Tab1.tsx remains the single source of truth.

import Eyebrow from './ui/Eyebrow';

interface KeyOption {
  value: string;
  label: string;
}

interface InputPanelProps {
  chordsInput: string;
  onChordsChange: (value: string) => void;
  keyOptions: KeyOption[];
  selectedKey: string;
  onKeyChange: (value: string) => void;
  profileOptions: KeyOption[];
  selectedProfile: string;
  onProfileChange: (value: string) => void;
  showEducational: boolean;
  onEducationalChange: (value: boolean) => void;
  loading: boolean;
  analyzed: boolean;
  onAnalyze: () => void;
  showCodeLink: boolean;
  onViewCode: () => void;
}

// Quick examples — vertical stack, each chip shows the Roman label on the
// left and the chord preview on the right. Hover paints the chip in coral.
const EXAMPLES: Array<{ label: string; chords: string }> = [
  { label: 'I – vi – IV – V',  chords: 'C  Am  F  G' },
  { label: 'ii – V – I',       chords: 'Dm  G7  Cmaj7' },
  { label: 'I – V – vi – IV',  chords: 'C  G  Am  F' },
  { label: 'Mixolydian ♭VII',  chords: 'G  F  C  G' },
];

const CodeIcon = ({ className = 'w-3.5 h-3.5' }: { className?: string }) => (
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

const inputClass =
  'w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent transition';

const InputPanel = ({
  chordsInput,
  onChordsChange,
  keyOptions,
  selectedKey,
  onKeyChange,
  profileOptions,
  selectedProfile,
  onProfileChange,
  showEducational,
  onEducationalChange,
  loading,
  analyzed,
  onAnalyze,
  showCodeLink,
  onViewCode,
}: InputPanelProps) => {
  // Disable the primary button when there's nothing to analyze or a request
  // is already in flight. Loading wins over analyzed for the label so the user
  // sees "Analyzing…" while a re-analyze is mid-flight.
  const buttonLabel = loading
    ? 'Analyzing…'
    : analyzed
      ? 'Re-analyze ↻'
      : 'Analyze progression →';

  return (
    <>
      {/* Title strip — never scrolls */}
      <div className="px-6 pt-6 pb-4 border-b border-slate-100 flex-shrink-0">
        <Eyebrow tone="primary" className="mb-1">Manual entry</Eyebrow>
        <h1 className="font-serif text-2xl font-semibold text-slate-900 tracking-tight">
          Chord progression
        </h1>
        <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
          Type chords. The analysis updates on the right.
        </p>
      </div>

      {/* Form body — scrolls if the panel ever overflows on a short viewport */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 min-h-0">
        <div>
          <label
            htmlFor="chords"
            className="block text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1.5"
          >
            Chords
          </label>
          <textarea
            id="chords"
            value={chordsInput}
            onChange={(e) => onChordsChange(e.target.value)}
            rows={3}
            className={`${inputClass} font-mono`}
            placeholder="C  Am  F  G"
            aria-describedby="chords-help"
          />
          <p id="chords-help" className="mt-1.5 text-[11px] text-slate-500 leading-relaxed">
            Letters with sharps, flats, slashes — separated by spaces, commas, or newlines.
          </p>
        </div>

        <div>
          <Eyebrow className="mb-2">Quick examples</Eyebrow>
          <div className="flex flex-col gap-1.5">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                type="button"
                onClick={() => onChordsChange(ex.chords)}
                className="group text-left text-xs bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded hover:border-primary-300 hover:bg-primary-50 transition flex items-center justify-between gap-2"
              >
                <span className="font-mono text-slate-700">{ex.label}</span>
                <span className="font-mono text-[10px] text-slate-400 group-hover:text-primary-700">
                  {ex.chords}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label
            htmlFor="key"
            className="block text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1.5"
          >
            Key hint
          </label>
          <select
            id="key"
            value={selectedKey}
            onChange={(e) => onKeyChange(e.target.value)}
            className={inputClass}
          >
            {keyOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="profile"
            className="block text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-1.5"
          >
            Profile focus
          </label>
          <select
            id="profile"
            value={selectedProfile}
            onChange={(e) => onProfileChange(e.target.value)}
            className={inputClass}
            data-testid="profile-selector"
          >
            {profileOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <label className="flex items-center gap-2 cursor-pointer select-none text-sm text-slate-700">
          <input
            type="checkbox"
            checked={showEducational}
            onChange={(e) => onEducationalChange(e.target.checked)}
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
          />
          Educational notes
        </label>
      </div>

      {/* Action footer — pinned at the bottom of the column */}
      <div className="border-t border-slate-100 px-6 py-4 space-y-2.5 bg-slate-50/40 flex-shrink-0">
        <button
          type="button"
          onClick={onAnalyze}
          disabled={loading || !chordsInput.trim()}
          className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold py-2.5 px-5 rounded-lg transition shadow-sm"
        >
          {buttonLabel}
        </button>
        {showCodeLink && (
          <button
            type="button"
            onClick={onViewCode}
            className="w-full inline-flex items-center justify-center gap-1.5 text-[12px] font-mono text-slate-500 hover:text-primary-700 transition py-1.5"
          >
            <CodeIcon />
            View as Python
          </button>
        )}
      </div>
    </>
  );
};

export default InputPanel;
