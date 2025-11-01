// Chord progression visualization - brings harmonic analysis to life with color
// This component renders chords horizontally with functional color coding and pattern brackets

import React from 'react';

interface PatternVisualization {
  chordColors?: string[];
  bracketRange: { start: number; end: number };
  labels: string[];
}

interface ChordProgressionVisualProps {
  chords: string[];
  patternVisualizations?: PatternVisualization[];
  highlightedChords?: number[]; // Indices of chords to highlight on hover
  hoveredBracketRange?: { start: number; end: number } | null; // Specific bracket range being hovered
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
  patternVisualizations = [],
  highlightedChords = [],
  hoveredBracketRange = null,
}) => {
  // Main play: Map chord colors based on ALL pattern visualizations
  const getChordStyle = (index: number) => {
    let colorKey: keyof typeof COLOR_MAP | undefined;

    // Check all pattern visualizations to find colors for this chord
    for (const viz of patternVisualizations) {
      const { bracketRange, chordColors } = viz;
      if (bracketRange && index >= bracketRange.start && index <= bracketRange.end && chordColors) {
        const bracketOffset = index - bracketRange.start;
        colorKey = chordColors[bracketOffset] as keyof typeof COLOR_MAP;
        break; // Use first matching pattern's color
      }
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

  // Big play: Assign brackets to vertical levels to prevent overlaps
  const assignBracketLevels = (visualizations: PatternVisualization[]): Map<number, number> => {
    const levelMap = new Map<number, number>(); // vizIndex -> level
    const levels: Array<Array<{ start: number; end: number }>> = []; // level -> occupied ranges

    // Helper: Check if two ranges overlap
    const rangesOverlap = (a: { start: number; end: number }, b: { start: number; end: number }) => {
      return !(a.end < b.start || b.end < a.start);
    };

    // Sort by start position for consistent level assignment
    const sortedVizs = visualizations.map((viz, idx) => ({ viz, idx }))
      .sort((a, b) => a.viz.bracketRange.start - b.viz.bracketRange.start);

    // Assign each bracket to the first available level
    for (const { viz, idx } of sortedVizs) {
      const range = viz.bracketRange;

      // Find first level where this bracket doesn't overlap
      let assignedLevel = 0;
      for (let level = 0; level < levels.length; level++) {
        const overlaps = levels[level].some(occupied => rangesOverlap(range, occupied));
        if (!overlaps) {
          assignedLevel = level;
          break;
        }
      }

      // If all levels have overlaps, create a new level
      if (assignedLevel === levels.length - 1 && levels[assignedLevel]?.some(occupied => rangesOverlap(range, occupied))) {
        assignedLevel = levels.length;
      }

      // Initialize level array if needed
      if (!levels[assignedLevel]) {
        levels[assignedLevel] = [];
      }

      // Assign bracket to this level
      levels[assignedLevel].push(range);
      levelMap.set(idx, assignedLevel);
    }

    return levelMap;
  };

  // 🎯 Single source of truth for all visualization sizing
  const LAYOUT_CONSTANTS = {
    // Horizontal spacing (matches actual rendered output)
    chordWidth: 8,        // rem - minWidth in JSX (line 256)
    arrowWidth: 1.5,      // rem - Tailwind w-6 = 1.5rem (line 264)
    gap: 1,               // rem - Tailwind gap-4 = 1rem (line 243), NOT 4rem!

    // Derived: total spacing per chord unit (chord + gap + arrow + gap)
    get unitSpacing() {
      return this.chordWidth + this.gap + this.arrowWidth + this.gap;
      // = 8 + 1 + 1.5 + 1 = 11.5rem
    },

    // Vertical spacing
    bracketSvgHeight: 20,     // px - SVG fixed height
    bracketMarginBottom: 0.5, // rem - mb-2
    labelLineHeight: 1,       // rem - text-xs line height
    labelGap: 0.25,           // rem - gap between stacked labels,
    firstBracketOffset: 4,  // NEW: rem - distance from chords to first bracket
    levelSpacing: 3.5,        // rem - spacing between bracket levels only

    // Positioning adjustments
    horizontalOffset: -0.5,  // rem - center brackets over chord boxes
  };

  // Calculate exact bracket width including all rendered elements
  const calculateBracketWidth = (startIdx: number, endIdx: number): number => {
    const chordCount = endIdx - startIdx + 1;
    const arrowCount = chordCount - 1;  // arrows only between chords
    const gapCount = (chordCount - 1) * 2; // gaps on both sides of each arrow

    return (
      LAYOUT_CONSTANTS.chordWidth * chordCount +
      LAYOUT_CONSTANTS.arrowWidth * arrowCount +
      LAYOUT_CONSTANTS.gap * gapCount + 1
    );
  };

  // Calculate exact horizontal position for bracket start
  const calculateBracketLeft = (startIdx: number): number => {
    // Each complete unit before startIdx takes up: chord + gap + arrow + gap
    return startIdx * LAYOUT_CONSTANTS.unitSpacing + LAYOUT_CONSTANTS.horizontalOffset;
  };

  // Big play: Render multiple brackets with vertical stacking
  const renderBrackets = () => {
    if (patternVisualizations.length === 0) return null;

    // Assign vertical levels to prevent overlaps
    const bracketLevels = assignBracketLevels(patternVisualizations);

    return patternVisualizations.map((viz, vizIndex) => {
      const { bracketRange, labels } = viz;
      const { start: startChordIndex, end: endChordIndex } = bracketRange;
      const level = bracketLevels.get(vizIndex) || 0;

      // Use new calculation functions - no magic numbers!
      const bracketWidthRem = calculateBracketWidth(startChordIndex, endChordIndex);
      const bracketLeftRem = calculateBracketLeft(startChordIndex);

      // Big play: Check if THIS bracket is the one being hovered
      const isBracketHovered = hoveredBracketRange &&
        hoveredBracketRange.start === startChordIndex &&
        hoveredBracketRange.end === endChordIndex;

      return (
        <div
          key={`bracket-${vizIndex}`}
          className="absolute flex flex-col items-center"
          style={{
            // Horizontal: Position using exact calculations
            left: `${bracketLeftRem}rem`,
            width: `${bracketWidthRem}rem`,
            // Vertical: separate first bracket position from level spacing
            top: `${LAYOUT_CONSTANTS.firstBracketOffset + (level * LAYOUT_CONSTANTS.levelSpacing)}rem`,
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
            {/* Single continuous bracket path - only highlight if THIS bracket is hovered */}
            <path
              d="M 2 0 L 2 12 L 98 12 L 98 0"
              className={`${isBracketHovered ? 'stroke-yellow-500' : 'stroke-slate-400'} transition-colors`}
              strokeWidth="2"
              fill="none"
              strokeLinecap="square"
            />
          </svg>

          {/* Pattern labels stacked vertically (PAC + IAC can share one bracket) */}
          {labels.length > 0 ? (
            <div className="flex flex-col items-center gap-1">
              {labels.map((label, idx) => (
                <span
                  key={idx}
                  className={`text-xs font-semibold ${isBracketHovered ? 'text-yellow-600' : 'text-slate-600'} transition-colors`}
                >
                  {label}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs font-semibold text-slate-600">Pattern</span>
          )}
        </div>
      );
    });
  };

  // Victory lap: Color legend for accessibility
  const ColorLegend = () => (
    <div className="flex flex-wrap gap-4 items-center p-3 bg-slate-50 rounded border border-slate-200">
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

  // Calculate dynamic padding for multiple bracket levels + stacked labels
  const getBracketPaddingBottom = () => {
    if (patternVisualizations.length === 0) return 0;

    // Assign levels to determine vertical stacking
    const bracketLevels = assignBracketLevels(patternVisualizations);
    const maxLevel = Math.max(...Array.from(bracketLevels.values()));
    // const numLevels = maxLevel + 1; // Convert 0-indexed to count

    // 🎯 Calculate actual height needed based on label content
    const maxLabelsPerBracket = Math.max(
      ...patternVisualizations.map(v => v.labels.length),
      1 // minimum 1 label
    );

    // Height per bracket level:
    // - SVG bracket (20px = 1.25rem)
    // - Bracket margin bottom (0.5rem)
    // - Labels: each label is 1rem line height
    // - Gaps between labels: 0.25rem each
    const heightPerLevel =
      LAYOUT_CONSTANTS.bracketSvgHeight / 16 +  // Convert 20px to rem
      LAYOUT_CONSTANTS.bracketMarginBottom +
      (maxLabelsPerBracket * LAYOUT_CONSTANTS.labelLineHeight) +
      ((maxLabelsPerBracket - 1) * LAYOUT_CONSTANTS.labelGap);

    // Total padding: levelSpacing is already in the top positioning,
    // so we only need space for the bracket levels themselves
    const totalHeight =
      (maxLevel * LAYOUT_CONSTANTS.levelSpacing) +  // Spacing between stacked levels
      heightPerLevel +                              // Height of bottom-most bracket
      2                                             // Extra padding for the top and bottom brackets

    return `${totalHeight}rem`;
  };

  return (
    <div className="space-y-2">
      {/* Chord progression display */}
      <div className="relative" style={{ paddingBottom: getBracketPaddingBottom() }}>
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M 9 5l7 7-7 7" />
                  </svg>
                )}
              </React.Fragment>
            );
          })}
        </div>
        {renderBrackets()}
      </div>
      {/* Color legend for WCAG accessibility */}
      <ColorLegend />
    </div>
  );
};
