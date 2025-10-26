// Chord progression visualization - brings harmonic analysis to life with color
// This component renders chords horizontally with functional color coding and pattern brackets

import React from 'react';

interface ChordProgressionVisualProps {
  chords: string[];
  chordColors?: string[]; // ["PD", "D", "T"] for predominant, dominant, tonic
  bracketRange?: { start: number; end: number };
  highlightedChords?: number[]; // Indices of chords to highlight on hover
}

// Opening move: Define our color palette mapping
const COLOR_MAP = {
  PD: {
    bg: 'bg-blue-500',
    text: 'text-blue-50',
    label: 'Setup',
    description: 'Predominant Function',
  },
  D: {
    bg: 'bg-orange-500',
    text: 'text-orange-50',
    label: 'Pattern',
    description: 'Dominant Function',
  },
  T: {
    bg: 'bg-green-500',
    text: 'text-green-50',
    label: 'Resolution',
    description: 'Tonic Function',
  },
};

export const ChordProgressionVisual: React.FC<ChordProgressionVisualProps> = ({
  chords,
  chordColors = [],
  bracketRange,
  highlightedChords = [],
}) => {
  // Main play: Map chord colors based on bracket range
  const getChordStyle = (index: number) => {
    let colorKey: keyof typeof COLOR_MAP | undefined;

    // Only apply colors to chords within the bracket range
    if (bracketRange && index >= bracketRange.start && index <= bracketRange.end) {
      const bracketOffset = index - bracketRange.start;
      colorKey = chordColors[bracketOffset] as keyof typeof COLOR_MAP;
    }

    const colors = colorKey ? COLOR_MAP[colorKey] : null;
    const isHighlighted = highlightedChords.includes(index);

    if (!colors) {
      // Fallback for chords without color metadata
      return {
        className: `bg-slate-200 text-slate-800 ${isHighlighted ? 'ring-4 ring-yellow-400' : ''}`,
        ariaLabel: chords[index],
      };
    }

    return {
      className: `${colors.bg} ${colors.text} ${isHighlighted ? 'ring-4 ring-yellow-400' : ''}`,
      ariaLabel: `${chords[index]} - ${colors.description}`,
    };
  };

  // Big play: Render the bracket under specified chord range
  const renderBracket = () => {
    if (!bracketRange) return null;

    // Extract pattern boundaries (chord array indices)
    const { start: startChordIndex, end: endChordIndex } = bracketRange;

    // Count how many chords are in the pattern
    const chordCount = endChordIndex - startChordIndex + 1;

    /**
     * Layout constants for chord progression visualization
     *
     * ⚠️ IMPORTANT: These values must be kept in sync with the CSS classes used in the JSX below.
     *
     * CHORD_BOX_WIDTH_REM:
     * - Matches the minWidth style on chord boxes (line 159: minWidth: '8rem')
     * - Represents the visual width of each colored chord box
     *
     * GAP_BETWEEN_CHORDS_REM:
     * - Represents the TOTAL horizontal space between adjacent chord box edges
     * - This is NOT just the flexbox gap! It accounts for the entire spacing structure:
     *   • gap-4 (1rem) - space between chord box and arrow (line 146)
     *   • w-6 (1.5rem) - width of the arrow SVG itself (line 167)
     *   • gap-4 (1rem) - space between arrow and next chord box (line 146)
     *   • 0.5rem - empirical adjustment for sub-pixel rendering quirks
     *   = 4rem total
     *
     * If you change the flexbox gap (line 146) or arrow width (line 167), you MUST
     * recalculate this constant to match the actual rendered spacing.
     */
    const CHORD_BOX_WIDTH_REM = 8;
    const GAP_BETWEEN_CHORDS_REM = 4;

    // Calculate bracket width: sum of chord widths plus gaps between them
    const bracketWidthRem =
      (CHORD_BOX_WIDTH_REM * chordCount) +
      (GAP_BETWEEN_CHORDS_REM * (chordCount - 1)) +
      0.5; // Yes, nothing ever lines up exactly, so... magic.

    return (
      <div
        className="absolute top-full mt-5 flex flex-col items-center"
        style={{
          // Position bracket starting under the first chord in pattern
          left: `calc(${startChordIndex} * (${GAP_BETWEEN_CHORDS_REM}rem + ${CHORD_BOX_WIDTH_REM}rem) - 1rem)`,
          width: `${bracketWidthRem}rem`,
        }}
      >
        {/* SVG bracket spanning full width */}
        <svg
          width="100%"
          height="20"
          viewBox="0 0 100 20"
          preserveAspectRatio="none"
          className="mb-2"
        >
          {/* Single continuous bracket path */}
          <path
            d="M 2 0 L 2 12 L 98 12 L 98 0"
            className={`${highlightedChords.length > 0 ? 'stroke-yellow-500' : 'stroke-slate-400'} transition-colors`}
            strokeWidth="2"
            fill="none"
            strokeLinecap="square"
          />
        </svg>

        {/* Pattern label as separate element (won't stretch) */}
        <span
          className={`text-xs font-semibold ${highlightedChords.length > 0 ? 'text-yellow-600' : 'text-slate-600'} transition-colors`}
        >
          Pattern
        </span>
      </div>
    );
  };

  // Victory lap: Color legend for accessibility
  const ColorLegend = () => (
    <div className="flex flex-wrap gap-4 items-center mt-20 p-3 bg-slate-50 rounded border border-slate-200">
      <span className="text-sm font-semibold text-slate-700">Color Guide:</span>
      {Object.entries(COLOR_MAP).map(([key, { bg, text, label, description }]) => (
        <div key={key} className="flex items-center gap-2">
          <div className={`w-6 h-6 rounded ${bg} ${text} flex items-center justify-center text-xs font-bold`}>
            {key}
          </div>
          <span className="text-sm text-slate-700">
            <span className="font-medium">{label}</span> ({description})
          </span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-2">
      {/* Chord progression display */}
      <div className="relative pb-0">
        <div className="flex flex-wrap gap-4 items-center">
          {chords.map((chord, index) => {
            const style = getChordStyle(index);
            const showArrow = index < chords.length - 1;

            return (
              <React.Fragment key={index}>
                <div
                  className={`
                    px-4 py-3 rounded-lg font-bold text-lg
                    transition-all duration-200
                    ${style.className}
                  `}
                  style={{ minWidth: '8rem', textAlign: 'center' }}
                  aria-label={style.ariaLabel}
                  role="listitem"
                >
                  {chord}
                </div>
                {showArrow && (
                  <svg
                    className="w-6 h-6 text-slate-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </React.Fragment>
            );
          })}
        </div>
          {renderBracket()}
      </div>
      {/* Color legend for WCAG accessibility */}
      <ColorLegend />
    </div>
  );
};
