// Pattern card — restyled with the new chrome (eyebrow + serif title +
// quiet borders, coral hover). Hover handlers still drive the bracket
// highlight in ChordProgressionVisual upstream.

import React, { useState } from 'react';
import type { EducationalCard, FullExplanation, PatternMatch, GlossaryEntry } from '../types/analysis';
import { BernsteinExplanation } from './BernsteinExplanation';
import Tag from './ui/Tag';

// We only consume a subset of PatternMatch's fields; opt into the relevant ones
// so test fixtures don't have to mock `evidence` or `section` arrays they
// don't care about.
type PatternMatchView = Pick<
  PatternMatch,
  'start' | 'end' | 'pattern_id' | 'name' | 'family' | 'score'
> & {
  glossary?: PatternMatch['glossary'];
  cadence_role?: PatternMatch['cadence_role'] | string;
  is_section_closure?: PatternMatch['is_section_closure'];
};

interface EnhancedPatternCardProps {
  pattern: PatternMatchView;
  educationalContent?: EducationalCard;
  explanation?: FullExplanation;
  onHover?: (patternId: string) => void;
  onLeave?: () => void;
}

// glossary may be a string label or a {definition, ...} object — pull the
// useful definition out either way without crashing on the unexpected shape.
const glossaryDefinition = (g: PatternMatchView['glossary']): string => {
  if (g == null) return '';
  if (typeof g === 'string') return g;
  return (g as GlossaryEntry).definition ?? '';
};

export const EnhancedPatternCard: React.FC<EnhancedPatternCardProps> = ({
  pattern,
  educationalContent,
  explanation,
  onHover,
  onLeave,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasEducation = !!educationalContent;
  const title = educationalContent?.title || pattern.name;
  const description = educationalContent?.summary || glossaryDefinition(pattern.glossary);
  const category = educationalContent?.category || pattern.family;

  return (
    <div
      className="bg-white border border-slate-200 hover:border-primary-300 hover:shadow-[0_2px_8px_rgba(15,23,42,0.06)] rounded-xl p-4 transition-all cursor-pointer"
      onMouseEnter={() => onHover?.(pattern.pattern_id)}
      onMouseLeave={() => onLeave?.()}
      role="region"
      aria-label={`Pattern: ${title}`}
    >
      {/* Eyebrow + title row */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-0.5">
            {pattern.pattern_id}
          </div>
          <h4 className="font-serif text-lg font-semibold text-slate-900 tracking-tight">
            {title}
          </h4>
        </div>
        {category && <Tag tone="primary">{category}</Tag>}
      </div>

      {description && (
        <p className="text-sm text-slate-600 leading-relaxed mb-3">{description}</p>
      )}

      {/* Meta row — score, span, optional cadence/closure tags. */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-3">
        <span className="font-mono tabular-nums text-slate-700 font-medium">
          score {(pattern.score * 100).toFixed(0)}%
        </span>
        <span className="text-slate-300">·</span>
        <span className="font-mono tabular-nums">
          chords {pattern.start}–{pattern.end}
        </span>
        {pattern.cadence_role && (
          <>
            <span className="text-slate-300">·</span>
            <Tag tone="indigo" className="text-[10px]">{pattern.cadence_role}</Tag>
          </>
        )}
        {pattern.is_section_closure && (
          <>
            <span className="text-slate-300">·</span>
            <Tag tone="emerald" className="text-[10px]">section closure</Tag>
          </>
        )}
      </div>

      {hasEducation && explanation && (
        <div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="text-primary-700 hover:text-primary-900 font-medium text-sm transition-colors flex items-center gap-1"
            aria-expanded={isExpanded}
          >
            {isExpanded ? 'Show less' : 'Learn more'}
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

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
