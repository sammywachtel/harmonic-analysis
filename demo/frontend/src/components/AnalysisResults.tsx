// Analysis results display - shows primary interpretation and alternatives
// This is the payoff moment - where users see the harmonic insights

import { useState } from 'react';
import type { AnalysisResponse } from '../types/analysis';
import { PatternSummaryCard } from './PatternSummaryCard';
import { ChordProgressionVisual } from './ChordProgressionVisual';

interface AnalysisResultsProps {
  results: AnalysisResponse;
  showEducational?: boolean;
  chords?: string[];
}

const AnalysisResults = ({ results, showEducational = true, chords = [] }: AnalysisResultsProps) => {
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [hoveredPatternId, setHoveredPatternId] = useState<string | null>(null);

  const { analysis, enhanced_summaries, educational } = results;
  const hasAlternatives = analysis.alternatives && analysis.alternatives.length > 0;
  const hasEducationalContent = educational?.available && educational?.content && educational.content.length > 0;

  // Main play: Get visualization hints - use first pattern with visualization data for default display
  const getDefaultVisualizationHints = () => {
    if (!educational?.content) return null;

    // Find first card with visualization hints
    const cardWithViz = educational.content.find(c => c.visualization);
    return cardWithViz?.visualization || null;
  };

  const defaultVisualizationHints = getDefaultVisualizationHints();

  // Time to tackle the tricky bit: Determine which chords to highlight with yellow ring
  const getHighlightedChords = () => {
    if (!hoveredPatternId || !educational?.content) return [];

    // Find the hovered pattern's bracket range
    const hoveredCard = educational.content.find(c => c.pattern_id === hoveredPatternId);
    if (!hoveredCard?.visualization?.bracket_range) return [];

    const { start, end } = hoveredCard.visualization.bracket_range;
    const indices: number[] = [];
    for (let i = start; i <= end; i++) {
      indices.push(i);
    }
    return indices;
  };

  return (
    <div className="space-y-6">
      {/* Summary section - high-level overview */}
      <div className="bg-info-50 border-l-4 border-info-500 p-4 rounded">
        <h3 className="font-semibold text-info-900 mb-2">Analysis Summary</h3>
        <p className="text-info-800">{results.summary}</p>
      </div>

      {/* Victory lap: Chord progression visualization */}
      {chords.length > 0 && (
        <div className="bg-white border border-slate-300 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Chord Progression</h3>
          <ChordProgressionVisual
            chords={chords}
            chordColors={defaultVisualizationHints?.chord_colors}
            bracketRange={defaultVisualizationHints?.bracket_range}
            highlightedChords={getHighlightedChords()}
          />
        </div>
      )}

      {/* Primary interpretation - the main event */}
      <div className="bg-white border border-slate-300 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-slate-900">Primary Interpretation</h3>
          <span className="text-sm font-medium text-slate-600">
            Confidence: {(analysis.primary.confidence * 100).toFixed(1)}%
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <span className="font-semibold text-slate-700">Key: </span>
            <span className="text-slate-900 text-lg">{analysis.primary.key_signature}</span>
          </div>

          <div>
            <span className="font-semibold text-slate-700">Roman Numerals: </span>
            <div className="mt-2 flex flex-wrap gap-2">
              {analysis.primary.roman_numerals.map((numeral, idx) => (
                <span
                  key={idx}
                  className="inline-block bg-primary-100 text-primary-800 px-3 py-1 rounded font-mono font-semibold"
                >
                  {numeral}
                </span>
              ))}
            </div>
          </div>

          {analysis.primary.interpretation && (
            <div>
              <span className="font-semibold text-slate-700">Interpretation: </span>
              <p className="text-slate-900 mt-1">{analysis.primary.interpretation}</p>
            </div>
          )}

          {analysis.primary.cadence_detection && (
            <div>
              <span className="font-semibold text-slate-700">Cadence: </span>
              <span className="text-slate-900">{analysis.primary.cadence_detection}</span>
            </div>
          )}
        </div>
      </div>

      {/* Pattern detection - extra insights */}
      {enhanced_summaries?.patterns_detected && enhanced_summaries.patterns_detected.length > 0 && (
        <div className="bg-success-50 border border-success-500 rounded-lg p-4">
          <h4 className="font-semibold text-success-900 mb-2">Patterns Detected</h4>
          <ul className="list-disc list-inside space-y-1 text-success-800">
            {enhanced_summaries.patterns_detected.map((pattern, idx) => (
              <li key={idx}>{pattern}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Big play: Educational content cards - rendered when toggle is on */}
      {showEducational && hasEducationalContent && (
        <div className="space-y-3">
          <h4 className="font-semibold text-slate-900 text-lg">Educational Content</h4>
          {educational.content!.map((card, idx) => {
            // Time to tackle the tricky bit: fetch explanation for this card
            const explanation = educational.explanations?.[card.pattern_id];
            return (
              <PatternSummaryCard
                key={card.pattern_id || idx}
                card={card}
                explanation={explanation}
                onHover={setHoveredPatternId}
                onLeave={() => setHoveredPatternId(null)}
              />
            );
          })}
        </div>
      )}

      {/* Alternative interpretations - toggle to reveal */}
      {hasAlternatives && (
        <div className="border border-slate-300 rounded-lg">
          <button
            onClick={() => setShowAlternatives(!showAlternatives)}
            className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition"
          >
            <h4 className="font-semibold text-slate-900">
              Alternative Interpretations ({analysis.alternatives!.length})
            </h4>
            <svg
              className={`w-5 h-5 text-slate-600 transition-transform ${
                showAlternatives ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showAlternatives && (
            <div className="border-t border-slate-300 p-4 space-y-4">
              {analysis.alternatives!.map((alt, idx) => (
                <div key={idx} className="bg-slate-50 p-4 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-semibold text-slate-900">{alt.key_signature}</h5>
                    <span className="text-sm text-slate-600">
                      Confidence: {(alt.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {alt.roman_numerals.map((numeral, i) => (
                      <span
                        key={i}
                        className="inline-block bg-slate-200 text-slate-800 px-2 py-1 rounded text-sm font-mono"
                      >
                        {numeral}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalysisResults;
