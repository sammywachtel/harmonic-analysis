// Opening move: Educational pattern card component for displaying pattern summaries
// This component presents educational content in a card-sized, accessible format

import React, { useState } from 'react';
import type { EducationalCard, FullExplanation } from '../types/analysis';
import { BernsteinExplanation } from './BernsteinExplanation';

interface PatternSummaryCardProps {
  card: EducationalCard;
  explanation?: FullExplanation;
  onHover?: (patternId: string) => void;
  onLeave?: () => void;
}

export const PatternSummaryCard: React.FC<PatternSummaryCardProps> = ({
  card,
  explanation,
  onHover,
  onLeave,
}) => {
  // Main play: State for expand/collapse
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className="bg-info-50 border border-info-200 rounded-lg p-4 mb-3 transition-all"
      role="region"
      aria-label={`Educational content: ${card.title}`}
      onMouseEnter={() => onHover?.(card.pattern_id)}
      onMouseLeave={() => onLeave?.()}
    >
      {/* Big play: Card header with title and category badge */}
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-slate-900">{card.title}</h3>
        {card.category && (
          <span className="text-xs font-medium px-2 py-1 bg-primary-100 text-primary-700 rounded-md">
            {card.category}
          </span>
        )}
      </div>

      {/* Victory lap: Summary text with proper typography */}
      <p className="text-base text-slate-700 leading-relaxed">{card.summary}</p>

      {/* Time to tackle the tricky bit: Learn more / Show less toggle */}
      {explanation && (
        <div className="mt-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-primary-700 hover:text-primary-900 font-medium text-sm transition-colors underline"
            aria-expanded={isExpanded}
          >
            {isExpanded ? 'Show less' : 'Learn more'}
          </button>

          {/* Here's where we reveal the full explanation */}
          {isExpanded && (
            <div className="mt-4 pt-4 border-t border-info-300">
              <BernsteinExplanation explanation={explanation} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
