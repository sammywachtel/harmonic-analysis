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
  const [showDetailedAnalysis, setShowDetailedAnalysis] = useState(false);
  const [hoveredPatternId, setHoveredPatternId] = useState<string | null>(null);

  const { analysis, enhanced_summaries, educational } = results;
  const hasAlternatives = analysis.alternatives && analysis.alternatives.length > 0;
  const hasEducationalContent = educational?.available && educational?.content && educational.content.length > 0;

  // Main play: Get visualization hints - use first pattern with visualization data for default display
  // Big play: Collect ALL pattern visualizations for multiple bracket support
  const getAllPatternVisualizations = () => {
    if (!educational?.content) return [];

    // Group cards by their bracket range
    const visualizationGroups: Array<{
      chordColors?: string[];
      bracketRange: { start: number; end: number };
      labels: string[];
    }> = [];

    // Main play: iterate through all cards and group by bracket range
    educational.content.forEach(card => {
      if (!card.visualization?.bracket_range) return;

      const bracket = card.visualization.bracket_range;

      // Find existing group with this bracket range
      const existingGroup = visualizationGroups.find(g =>
        g.bracketRange.start === bracket.start && g.bracketRange.end === bracket.end
      );

      if (existingGroup) {
        // Add label to existing group
        existingGroup.labels.push(card.title);
      } else {
        // Create new group
        visualizationGroups.push({
          chordColors: card.visualization.chord_colors,
          bracketRange: bracket,
          labels: [card.title]
        });
      }
    });

    // Victory lap: sort by start position for consistent rendering
    return visualizationGroups.sort((a, b) => a.bracketRange.start - b.bracketRange.start);
  };

  const allPatternVisualizations = getAllPatternVisualizations();

  // Time to tackle the tricky bit: Determine which chords and bracket to highlight
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

  // Big play: Get the hovered bracket range for selective bracket highlighting
  const getHoveredBracketRange = () => {
    if (!hoveredPatternId || !educational?.content) return null;

    const hoveredCard = educational.content.find(c => c.pattern_id === hoveredPatternId);
    return hoveredCard?.visualization?.bracket_range || null;
  };

  // Helper: Get analysis type badge color
  const getTypeBadgeColor = (type?: string) => {
    switch (type) {
      case 'functional':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'modal':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'chromatic':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary section - high-level overview */}
      <div className="bg-info-50 border-l-4 border-info-500 p-4 rounded">
        <h3 className="font-semibold text-info-900 mb-2">Analysis Summary</h3>
        <p className="text-info-800">{results.summary}</p>
      </div>

      {/* Victory lap: Chord progression visualization with multiple pattern support */}
      {chords.length > 0 && (
        <div className="bg-white border border-slate-300 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Chord Progression</h3>
          <ChordProgressionVisual
            chords={chords}
            patternVisualizations={allPatternVisualizations}
            highlightedChords={getHighlightedChords()}
            hoveredBracketRange={getHoveredBracketRange()}
          />
        </div>
      )}

      {/* Primary interpretation - the main event */}
      <div className="bg-white border border-slate-300 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold text-slate-900">Primary Interpretation</h3>
            {analysis.primary.type && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getTypeBadgeColor(analysis.primary.type)}`}>
                {analysis.primary.type.charAt(0).toUpperCase() + analysis.primary.type.slice(1)}
              </span>
            )}
          </div>
          <span className="text-sm font-medium text-slate-600">
            Confidence: {(analysis.primary.confidence * 100).toFixed(1)}%
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <span className="font-semibold text-slate-700">Key: </span>
            <span className="text-slate-900 text-lg">{analysis.primary.key_signature}</span>
            {analysis.primary.mode && (
              <span className="ml-2 text-slate-600">({analysis.primary.mode})</span>
            )}
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

          {/* Confidence breakdown */}
          {(analysis.primary.functional_confidence !== undefined ||
            analysis.primary.modal_confidence !== undefined ||
            analysis.primary.chromatic_confidence !== undefined) && (
            <div className="border-t border-slate-200 pt-3 mt-3">
              <span className="font-semibold text-slate-700 block mb-2">Confidence Breakdown:</span>
              <div className="grid grid-cols-3 gap-3 text-sm">
                {analysis.primary.functional_confidence !== undefined && (
                  <div>
                    <span className="text-slate-600">Functional: </span>
                    <span className="font-medium text-blue-700">
                      {(analysis.primary.functional_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {analysis.primary.modal_confidence !== undefined && (
                  <div>
                    <span className="text-slate-600">Modal: </span>
                    <span className="font-medium text-purple-700">
                      {(analysis.primary.modal_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {analysis.primary.chromatic_confidence !== undefined && (
                  <div>
                    <span className="text-slate-600">Chromatic: </span>
                    <span className="font-medium text-orange-700">
                      {(analysis.primary.chromatic_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {analysis.primary.reasoning && (
            <div className="border-t border-slate-200 pt-3 mt-3">
              <span className="font-semibold text-slate-700">Reasoning: </span>
              <p className="text-slate-900 mt-1 text-sm">{analysis.primary.reasoning}</p>
            </div>
          )}

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

      {/* Detected Patterns - detailed view */}
      {analysis.primary.patterns && analysis.primary.patterns.length > 0 && (
        <div className="bg-white border border-slate-300 rounded-lg shadow-sm">
          <button
            onClick={() => setShowDetailedAnalysis(!showDetailedAnalysis)}
            className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition"
          >
            <h4 className="font-semibold text-slate-900">
              Detected Patterns ({analysis.primary.patterns.length})
            </h4>
            <svg
              className={`w-5 h-5 text-slate-600 transition-transform ${
                showDetailedAnalysis ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showDetailedAnalysis && (
            <div className="border-t border-slate-300 p-4 space-y-3">
              {analysis.primary.patterns.map((pattern, idx) => (
                <div key={idx} className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h5 className="font-semibold text-slate-900">{pattern.name}</h5>
                      <span className="text-xs text-slate-600 font-mono">{pattern.pattern_id}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-slate-900">
                        Score: {(pattern.score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-slate-600">
                        Chords {pattern.start}–{pattern.end}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`px-2 py-0.5 rounded ${
                      pattern.family === 'functional' ? 'bg-blue-100 text-blue-800' :
                      pattern.family === 'modal' ? 'bg-purple-100 text-purple-800' :
                      'bg-orange-100 text-orange-800'
                    }`}>
                      {pattern.family}
                    </span>
                    {pattern.is_section_closure && (
                      <span className="px-2 py-0.5 rounded bg-green-100 text-green-800">
                        Section Closure
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal characteristics */}
      {analysis.primary.modal_characteristics && analysis.primary.modal_characteristics.length > 0 && (
        <div className="bg-purple-50 border border-purple-300 rounded-lg p-4">
          <h4 className="font-semibold text-purple-900 mb-2">Modal Characteristics</h4>
          <ul className="list-disc list-inside space-y-1 text-purple-800">
            {analysis.primary.modal_characteristics.map((char, idx) => (
              <li key={idx}>{char}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Modal evidence */}
      {analysis.primary.modal_evidence && analysis.primary.modal_evidence.length > 0 && (
        <div className="bg-purple-50 border border-purple-300 rounded-lg p-4">
          <h4 className="font-semibold text-purple-900 mb-2">Modal Evidence</h4>
          <div className="space-y-2">
            {analysis.primary.modal_evidence.map((evidence, idx) => (
              <div key={idx} className="text-sm">
                <span className="font-medium text-purple-900">{evidence.type}:</span>
                <span className="text-purple-800 ml-2">{evidence.description}</span>
                <span className="text-purple-700 ml-2">
                  (strength: {(evidence.strength * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chromatic elements */}
      {analysis.primary.chromatic_elements && analysis.primary.chromatic_elements.length > 0 && (
        <div className="bg-orange-50 border border-orange-300 rounded-lg p-4">
          <h4 className="font-semibold text-orange-900 mb-2">Chromatic Elements</h4>
          <ul className="list-disc list-inside space-y-1 text-orange-800">
            {analysis.primary.chromatic_elements.map((element, idx) => (
              <li key={idx}>{element}</li>
            ))}
          </ul>
        </div>
      )}

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
