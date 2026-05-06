// Chord progression visualization. Layout-wise, this is a CSS Grid where:
//   - Row 1: chord cards (one per column)
//   - Rows 2+: pattern brackets, each spanning the columns it covers
//
// CSS Grid solves the old layout's biggest pain: when chord lists wrapped to
// multiple lines, the absolute-positioned brackets had no way to follow the
// wrap and ended up floating off-canvas. With grid spans, the brackets are
// in the same coordinate system as the chord cards — they always line up.
//
// On overflow we scroll horizontally instead of wrapping, which keeps every
// pattern's bracket on its own line below its chord cards.

import React from 'react';

interface PatternVisualization {
  chordColors?: string[];
  bracketRange: { start: number; end: number };
  labels: string[];
}

interface ChordProgressionVisualProps {
  chords: string[];
  patternVisualizations?: PatternVisualization[];
  /** Indices of chords to highlight on hover. */
  highlightedChords?: number[];
  /** The specific bracket range currently being hovered, for selective highlight. */
  hoveredBracketRange?: { start: number; end: number } | null;
}

// Function color tokens. The reskin uses these on top stripes (1.5px) so each
// card stays predominantly white with an editorial accent.
const COLOR_MAP = {
  PD: {
    bg: 'bg-indigo-500',
    text: 'text-indigo-50',
    stripe: 'bg-indigo-500',
    eyebrow: 'text-indigo-700',
    tag: 'bg-indigo-50 text-indigo-800 border-indigo-200',
    label: 'Setup',
    description: 'Predominant Function',
  },
  D: {
    bg: 'bg-amber-500',
    text: 'text-amber-50',
    stripe: 'bg-amber-500',
    eyebrow: 'text-amber-700',
    tag: 'bg-amber-50 text-amber-800 border-amber-200',
    label: 'Pattern',
    description: 'Dominant Function',
  },
  T: {
    bg: 'bg-emerald-500',
    text: 'text-emerald-50',
    stripe: 'bg-emerald-500',
    eyebrow: 'text-emerald-700',
    tag: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    label: 'Resolution',
    description: 'Tonic Function',
  },
} as const;

type ColorKey = keyof typeof COLOR_MAP;

// Stack overlapping brackets onto separate grid rows. Earlier-starting bracket
// gets the lower row; conflicts push to the next.
const assignBracketLevels = (
  visualizations: PatternVisualization[],
): Map<number, number> => {
  const overlap = (
    a: { start: number; end: number },
    b: { start: number; end: number },
  ) => !(a.end < b.start || b.end < a.start);

  const sorted = visualizations
    .map((viz, idx) => ({ viz, idx }))
    .sort((a, b) => a.viz.bracketRange.start - b.viz.bracketRange.start);

  const levels: Array<Array<{ start: number; end: number }>> = [];
  const out = new Map<number, number>();

  for (const { viz, idx } of sorted) {
    const range = viz.bracketRange;
    let assigned = -1;
    for (let lv = 0; lv < levels.length; lv++) {
      if (!levels[lv].some((occ) => overlap(range, occ))) {
        assigned = lv;
        break;
      }
    }
    if (assigned === -1) {
      assigned = levels.length;
      levels.push([]);
    }
    levels[assigned].push(range);
    out.set(idx, assigned);
  }
  return out;
};

export const ChordProgressionVisual: React.FC<ChordProgressionVisualProps> = ({
  chords,
  patternVisualizations = [],
  highlightedChords = [],
  hoveredBracketRange = null,
}) => {
  // Pick the function color for chord N from the first matching pattern, if any.
  const colorForChord = (index: number): ColorKey | null => {
    for (const viz of patternVisualizations) {
      const { bracketRange, chordColors } = viz;
      if (
        bracketRange &&
        index >= bracketRange.start &&
        index <= bracketRange.end &&
        chordColors
      ) {
        const offset = index - bracketRange.start;
        const key = chordColors[offset] as ColorKey | undefined;
        if (key && COLOR_MAP[key]) return key;
      }
    }
    return null;
  };

  const bracketLevels = assignBracketLevels(patternVisualizations);
  const maxLevel = bracketLevels.size > 0
    ? Math.max(...Array.from(bracketLevels.values()))
    : -1;
  const bracketRowCount = maxLevel + 1;

  // Each chord gets one column. The min keeps cards readable on small screens;
  // the fr lets them grow to fill the container when there are few chords.
  const gridTemplateColumns = chords.length > 0
    ? `repeat(${chords.length}, minmax(5.5rem, 1fr))`
    : 'auto';

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto -mx-2 px-2">
        <div
          className="grid gap-x-2 gap-y-3"
          style={{ gridTemplateColumns, minWidth: chords.length > 0 ? `${chords.length * 5.5}rem` : 'auto' }}
        >
          {/* Row 1: chord cards. */}
          {chords.map((chord, index) => {
            const colorKey = colorForChord(index);
            const colors = colorKey ? COLOR_MAP[colorKey] : null;
            const isHighlighted = highlightedChords.includes(index);
            const ariaLabel = colors ? `${chord} - ${colors.description}` : chord;

            return (
              <div
                key={`chord-${index}`}
                className={`relative bg-white border border-slate-200 rounded-xl pt-3 pb-2.5 px-2 text-center transition-all ${
                  isHighlighted
                    ? `${colors?.bg ?? 'bg-slate-200'} ${colors?.text ?? 'text-slate-900'} ring-2 ring-primary-500 ring-offset-1 border-transparent shadow-[0_2px_8px_rgba(15,23,42,0.06)]`
                    : ''
                }`}
                style={{ gridColumn: `${index + 1} / ${index + 2}`, gridRow: 1 }}
                role="listitem"
                aria-label={ariaLabel}
              >
                {/* Top stripe — solid 4px coloured bar. */}
                {colors ? (
                  <div className={`absolute top-0 left-0 right-0 h-1 rounded-t-xl ${colors.stripe}`} />
                ) : (
                  <div className="absolute top-0 left-0 right-0 h-1 rounded-t-xl bg-slate-200" />
                )}
                <div className="font-serif text-xl font-semibold text-slate-900 tracking-tight leading-tight py-1">
                  {chord}
                </div>
              </div>
            );
          })}

          {/* Rows 2+: pattern brackets. Each one occupies a single grid row,
              spanning columns from start+1 to end+2 (inclusive end). */}
          {patternVisualizations.map((viz, vizIndex) => {
            const level = bracketLevels.get(vizIndex) ?? 0;
            const { start, end } = viz.bracketRange;
            const isHovered =
              hoveredBracketRange?.start === start && hoveredBracketRange?.end === end;

            return (
              <div
                key={`bracket-${vizIndex}`}
                className="flex flex-col items-center"
                style={{
                  gridColumn: `${start + 1} / ${end + 2}`,
                  gridRow: 2 + level,
                }}
              >
                <svg
                  width="100%"
                  height="14"
                  viewBox="0 0 100 14"
                  preserveAspectRatio="none"
                  className="-mt-1"
                  aria-hidden="true"
                >
                  <path
                    d="M 1 0 L 1 8 L 99 8 L 99 0"
                    className={`${
                      isHovered ? 'stroke-primary-600' : 'stroke-slate-400'
                    } transition-colors`}
                    strokeWidth="1.5"
                    fill="none"
                  />
                </svg>
                <div className="mt-1.5 flex flex-col items-center gap-0.5">
                  {(viz.labels.length > 0 ? viz.labels : ['Pattern']).map((label, i) => (
                    <span
                      key={i}
                      className={`font-serif italic text-xs leading-tight whitespace-nowrap ${
                        isHovered ? 'text-primary-700 font-semibold' : 'text-slate-600 font-medium'
                      }`}
                    >
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}

          {/* Spacer row to reserve vertical space below the brackets. */}
          {bracketRowCount > 0 && (
            <div
              aria-hidden="true"
              style={{ gridColumn: `1 / ${chords.length + 1}`, gridRow: 2 + bracketRowCount, height: '0.25rem' }}
            />
          )}
        </div>
      </div>

      {/* Color legend — eyebrow + tone tags, matches the rest of the chrome. */}
      {patternVisualizations.some((viz) => viz.chordColors && viz.chordColors.length > 0) && (
        <div className="flex flex-wrap gap-3 items-center px-3 py-2.5 bg-slate-50 rounded-lg border border-slate-200">
          <span className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">
            Color guide
          </span>
          {(['PD', 'D', 'T'] as ColorKey[]).map((key) => {
            const c = COLOR_MAP[key];
            return (
              <div key={key} className="flex items-center gap-1.5 text-xs">
                <span
                  className={`inline-flex items-center justify-center w-6 h-5 rounded-md border font-mono font-semibold ${c.tag}`}
                >
                  {key}
                </span>
                <span className="text-slate-700">
                  <span className="font-medium text-slate-900">{c.label}</span>
                  <span className="text-slate-500 ml-1">({c.description})</span>
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
