// Roman numerals laid out as a notation-style score line: a horizontal row of
// bordered cells, each holding an italic serif numeral above either the actual
// chord (Tab 1) or just an index (Tab 2). The whole thing scrolls horizontally
// on small screens.

import Eyebrow from './ui/Eyebrow';

interface RomanScoreLineProps {
  /** Roman numerals, in playing order. */
  numerals: string[];
  /** Optional matching chord labels (Tab 1 mode). When present, shown below numerals. */
  chords?: string[];
  /** Eyebrow text — defaults to "Roman numerals · N chords". */
  label?: string;
  /** Visual size: "lg" for Tab 1 (text-2xl), "md" for Tab 2 (text-lg). */
  size?: 'md' | 'lg';
  className?: string;
}

const RomanScoreLine = ({
  numerals,
  chords,
  label,
  size = 'lg',
  className = '',
}: RomanScoreLineProps) => {
  const eyebrowText = label ?? `Roman numerals · ${numerals.length} ${numerals.length === 1 ? 'chord' : 'chords'}`;

  const numeralSize = size === 'lg' ? 'text-2xl' : 'text-lg';
  const cellMinWidth = size === 'lg' ? 'min-w-[3.5rem]' : 'min-w-[2.75rem]';

  return (
    <div className={className}>
      <Eyebrow tone="slate" className="mb-3">{eyebrowText}</Eyebrow>
      <div className="overflow-x-auto -mx-1 px-1">
        <div className="inline-flex items-end gap-0 border-b border-slate-200">
          {numerals.map((numeral, i) => (
            <div
              key={`${numeral}-${i}`}
              className={`flex flex-col items-center px-4 py-2 border-r border-slate-200 last:border-r-0 ${cellMinWidth}`}
            >
              <span className={`font-serif italic ${numeralSize} text-primary-800 font-semibold leading-none`}>
                {numeral}
              </span>
              {chords && chords[i] != null ? (
                <span className="font-mono text-[11px] text-slate-500 mt-1.5">
                  {chords[i]}
                </span>
              ) : (
                <span className="font-mono text-[10px] text-slate-400 mt-1.5 tabular-nums">
                  {i + 1}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RomanScoreLine;
