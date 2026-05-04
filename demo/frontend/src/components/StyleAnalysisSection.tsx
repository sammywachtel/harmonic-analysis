// Expandable section showing per-style analysis breakdown
// Progressive disclosure: collapsed by default, sorted by confidence

import { useState } from 'react';
import type { StyleAnalysisDetail } from '../types/analysis';
import StyleDetailCard from './StyleDetailCard';

interface StyleAnalysisSectionProps {
  styleAnalysis: Record<string, StyleAnalysisDetail>;
  dominantStyle?: string;
}

const StyleAnalysisSection = ({ styleAnalysis, dominantStyle }: StyleAnalysisSectionProps) => {
  const [expanded, setExpanded] = useState(false);

  // Opening move: sort styles by confidence (highest first)
  const sortedStyles = Object.entries(styleAnalysis).sort(
    ([, a], [, b]) => b.confidence - a.confidence
  );

  const styleCount = sortedStyles.length;

  // Guard: no styles to show
  if (styleCount === 0) {
    return null;
  }

  return (
    <div className="border border-slate-300 rounded-lg" data-testid="style-analysis-section">
      {/* Toggle button with expand/collapse chevron */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition rounded-lg"
        aria-expanded={expanded}
        aria-controls="style-analysis-details"
        aria-label={`View analysis through ${styleCount} different musical styles`}
        data-testid="style-analysis-toggle"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-5 h-5 text-slate-600 transition-transform ${
              expanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          <h4 className="font-semibold text-slate-900">
            View analysis through different styles ({styleCount})
          </h4>
        </div>
      </button>

      {/* Expanded content: style detail cards */}
      {expanded && (
        <div
          id="style-analysis-details"
          className="border-t border-slate-300 p-4 space-y-4"
          data-testid="style-cards-container"
        >
          {sortedStyles.map(([styleName, detail]) => (
            <StyleDetailCard
              key={styleName}
              styleName={styleName}
              detail={detail}
              isDominant={styleName === dominantStyle}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default StyleAnalysisSection;
