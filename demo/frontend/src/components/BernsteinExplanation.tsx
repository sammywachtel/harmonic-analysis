// Opening move: Bernstein-style explanation component with progressive disclosure
// This component renders engaging, hierarchical educational content with optional technical depth

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { FullExplanation } from '../types/analysis';

interface BernsteinExplanationProps {
  explanation: FullExplanation;
}

export const BernsteinExplanation: React.FC<BernsteinExplanationProps> = ({ explanation }) => {
  // Main play: State for Layer 2 technical notes expansion
  const [showTechnical, setShowTechnical] = useState(false);

  return (
    <div className="space-y-6">
      {/* Big play: Hook - attention-grabbing opening */}
      <div className="text-lg text-slate-800 italic border-l-4 border-primary-500 pl-4 py-2 bg-primary-50 rounded-r-lg">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation.hook}</ReactMarkdown>
      </div>

      {/* Main section: Breakdown - hierarchical key points */}
      <div>
        <h4 className="text-lg font-semibold text-slate-900 mb-3">The Essentials</h4>
        <div className="space-y-2">
          {explanation.breakdown.map((point, idx) => (
            <div key={idx} className="text-slate-700 leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{point}</ReactMarkdown>
            </div>
          ))}
        </div>
      </div>

      {/* Victory lap: Story - narrative context */}
      <div>
        <h4 className="text-lg font-semibold text-slate-900 mb-3">The Story</h4>
        <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation.story}</ReactMarkdown>
        </div>
      </div>

      {/* Time to tackle the tricky bit: Composers - who uses this */}
      <div>
        <h4 className="text-lg font-semibold text-slate-900 mb-3">In the Hands of Masters</h4>
        <div className="text-slate-700 leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation.composers}</ReactMarkdown>
        </div>
      </div>

      {/* Here's where we showcase specific examples */}
      <div>
        <h4 className="text-lg font-semibold text-slate-900 mb-3">Listen For It Here</h4>
        <ul className="space-y-2 list-none">
          {explanation.examples.map((example, idx) => (
            <li key={idx} className="text-slate-700 leading-relaxed pl-4 border-l-2 border-info-300">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{example}</ReactMarkdown>
            </li>
          ))}
        </ul>
      </div>

      {/* Final whistle: Try this - actionable practice */}
      <div className="bg-success-50 border border-success-200 rounded-lg p-4">
        <h4 className="text-lg font-semibold text-slate-900 mb-2">Try This</h4>
        <div className="text-slate-700 leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation.try_this}</ReactMarkdown>
        </div>
      </div>

      {/* Layer 2: Optional technical depth (progressive disclosure) */}
      {explanation.technical_notes && (
        <div className="border-t border-slate-300 pt-4">
          <button
            onClick={() => setShowTechnical(!showTechnical)}
            className="flex items-center text-primary-700 hover:text-primary-900 font-medium transition-colors"
            aria-expanded={showTechnical}
          >
            <span className="mr-2">{showTechnical ? '▼' : '▶'}</span>
            <span>{showTechnical ? 'Hide' : 'Show'} Technical Details</span>
          </button>

          {showTechnical && (
            <div className="mt-4 space-y-4 bg-slate-50 border border-slate-200 rounded-lg p-4">
              {explanation.technical_notes.voice_leading && (
                <div>
                  <h5 className="text-md font-semibold text-slate-900 mb-2">Voice Leading</h5>
                  <div className="text-slate-700 text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {explanation.technical_notes.voice_leading}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {explanation.technical_notes.theoretical_depth && (
                <div>
                  <h5 className="text-md font-semibold text-slate-900 mb-2">Theoretical Depth</h5>
                  <div className="text-slate-700 text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {explanation.technical_notes.theoretical_depth}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {explanation.technical_notes.historical_context && (
                <div>
                  <h5 className="text-md font-semibold text-slate-900 mb-2">Historical Context</h5>
                  <div className="text-slate-700 text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {explanation.technical_notes.historical_context}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
