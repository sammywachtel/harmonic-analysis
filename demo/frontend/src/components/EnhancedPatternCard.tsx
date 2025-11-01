// Enhanced pattern card - unified display for patterns with or without educational content
// This component combines technical pattern data with educational content when available

import React, { useState } from 'react';
import type { EducationalCard, FullExplanation } from '../types/analysis';
import { BernsteinExplanation } from './BernsteinExplanation';

// Pattern match structure from analysis.primary.patterns
interface PatternMatch {
  start: number;
  end: number;
  pattern_id: string;
  name: string;
  family: string;
  score: number;
  glossary?: {
    definition?: string;
    example_in_C_major?: string;
    term?: string;
    type?: string;
  };
  cadence_role?: string;
  is_section_closure?: boolean;
}

interface EnhancedPatternCardProps {
  pattern: PatternMatch;
  educationalContent?: EducationalCard;
  explanation?: FullExplanation;
  onHover?: (patternId: string) => void;
  onLeave?: () => void;
}

export const EnhancedPatternCard: React.FC<EnhancedPatternCardProps> = ({
  pattern,
  educationalContent,
  explanation,
  onHover,
  onLeave,
}) => {
  // Main play: State for expand/collapse
  const [isExpanded, setIsExpanded] = useState(false);

  // Big play: Determine card type and get display values
  const hasEducation = !!educationalContent;
  const title = educationalContent?.title || pattern.name;
  const description = educationalContent?.summary || pattern.glossary?.definition || '';
  const category = educationalContent?.category || pattern.family;

  return (
    <div
      className="bg-white border border-slate-300 rounded-lg p-4 hover:shadow-md transition-all cursor-pointer"
      onMouseEnter={() => onHover?.(pattern.pattern_id)}
      onMouseLeave={() => onLeave?.()}
      role="region"
      aria-label={`Pattern: ${title}`}
    >
      {/* Header: Title + Category Badge */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-slate-900">{title}</h4>
          <p className="text-xs text-slate-600 font-mono mt-0.5">{pattern.pattern_id}</p>
        </div>
        {category && (
          <span className="text-xs font-medium px-2 py-1 bg-primary-100 text-primary-700 rounded-md whitespace-nowrap ml-2">
            {category}
          </span>
        )}
      </div>

      {/* Description: Educational summary or glossary fallback */}
      {description && (
        <p className="text-sm text-slate-700 leading-relaxed mb-3">{description}</p>
      )}

      {/* Metadata: Score, range, badges */}
      <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600 mb-3">
        <span className="font-medium text-slate-900">
          Score: {(pattern.score * 100).toFixed(0)}%
        </span>
        <span className="text-slate-400">•</span>
        <span>Chords {pattern.start}–{pattern.end}</span>
        {pattern.cadence_role && (
          <>
            <span className="text-slate-400">•</span>
            <span className="px-2 py-0.5 rounded bg-info-100 text-info-800 text-xs font-medium">
              {pattern.cadence_role}
            </span>
          </>
        )}
        {pattern.is_section_closure && (
          <span className="px-2 py-0.5 rounded bg-green-100 text-green-800 text-xs font-medium">
            Section Closure
          </span>
        )}
      </div>

      {/* Victory lap: Learn More button - only if educational explanation exists */}
      {hasEducation && explanation && (
        <div>
          <button
            onClick={(e) => {
              e.stopPropagation(); // Prevent card hover from interfering
              setIsExpanded(!isExpanded);
            }}
            className="text-primary-700 hover:text-primary-900 font-medium text-sm transition-colors underline"
            aria-expanded={isExpanded}
          >
            {isExpanded ? 'Show less' : 'Learn more'}
          </button>

          {/* Here's where we reveal the full Bernstein-style explanation */}
          {isExpanded && (
            <div className="mt-4 pt-4 border-t border-slate-200">
              <BernsteinExplanation explanation={explanation} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
