// Multi-profile disclosure — wraps the per-style analysis cards in a
// SectionCard chrome with an expand/collapse toggle. All test selectors
// (data-testid, aria-expanded, aria-controls) are preserved so e2e stays green.

import { useState } from 'react';
import type { StyleAnalysisDetail } from '../types/analysis';
import StyleDetailCard from './StyleDetailCard';
import SectionCard from './ui/SectionCard';

interface StyleAnalysisSectionProps {
  styleAnalysis: Record<string, StyleAnalysisDetail>;
  dominantStyle?: string;
}

const StyleAnalysisSection = ({ styleAnalysis, dominantStyle }: StyleAnalysisSectionProps) => {
  const [expanded, setExpanded] = useState(false);

  // Highest confidence first — give the user the strongest reading at the top.
  const sortedStyles = Object.entries(styleAnalysis).sort(
    ([, a], [, b]) => b.confidence - a.confidence,
  );

  const styleCount = sortedStyles.length;
  if (styleCount === 0) return null;

  return (
    <SectionCard
      eyebrow="Multi-profile"
      title={`View analysis through different styles (${styleCount})`}
      action={
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-controls="style-analysis-details"
          aria-label={`View analysis through ${styleCount} different musical styles`}
          data-testid="style-analysis-toggle"
          className="style-analysis-toggle text-sm text-primary-700 hover:text-primary-900 font-medium flex items-center gap-1"
        >
          {expanded ? 'Hide' : 'Show'}
          <svg
            className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      }
      className="style-analysis-section"
      bodyClassName={expanded ? 'p-6' : 'px-6 py-4'}
    >
      <div data-testid="style-analysis-section">
        {expanded ? (
          <div
            id="style-analysis-details"
            className="space-y-4"
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
        ) : (
          <p className="text-sm text-slate-500">
            Each musical style reads the progression a little differently. Open to compare —
            confidence and characteristic patterns side by side.
          </p>
        )}
      </div>
    </SectionCard>
  );
};

export default StyleAnalysisSection;
