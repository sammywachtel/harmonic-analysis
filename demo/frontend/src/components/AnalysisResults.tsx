// Analysis results display - shows primary interpretation and alternatives
// This is the payoff moment - where users see the harmonic insights

import { useState } from 'react';
import type { AnalysisResponse } from '../types/analysis';
import { EnhancedPatternCard } from './EnhancedPatternCard';
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

  // Main play: Get visualization hints - use first pattern with visualization data for default display
  // Big play: Collect ALL pattern visualizations for multiple bracket support
  const getAllPatternVisualizations = () => {
    // Group cards by their bracket range
    const visualizationGroups: Array<{
      chordColors?: string[];
      bracketRange: { start: number; end: number };
      labels: string[];
    }> = [];

    // Opening move: Create visualizations from ALL patterns (educational or not)
    if (analysis.primary.patterns && analysis.primary.patterns.length > 0) {
      analysis.primary.patterns.forEach(pattern => {
        // Find matching educational content if available
        const eduContent = educational?.content?.find(
          card => card.pattern_id === pattern.pattern_id
        );

        // Use educational visualization if available, otherwise create from pattern data
        const bracket = eduContent?.visualization?.bracket_range
          ? eduContent.visualization.bracket_range
          : { start: pattern.start, end: pattern.end };

        const label = eduContent?.title || pattern.name;
        const chordColors = eduContent?.visualization?.chord_colors;

        // Find existing group with this bracket range
        const existingGroup = visualizationGroups.find(g =>
          g.bracketRange.start === bracket.start && g.bracketRange.end === bracket.end
        );

        if (existingGroup) {
          // Add label to existing group
          existingGroup.labels.push(label);
        } else {
          // Create new group
          visualizationGroups.push({
            chordColors: chordColors,
            bracketRange: bracket,
            labels: [label]
          });
        }
      });
    }

    // Victory lap: sort by start position for consistent rendering
    return visualizationGroups.sort((a, b) => a.bracketRange.start - b.bracketRange.start);
  };

  const allPatternVisualizations = getAllPatternVisualizations();

  // Time to tackle the tricky bit: Determine which chords and bracket to highlight
  const getHighlightedChords = () => {
    if (!hoveredPatternId) return [];

    // Try to find bracket range from educational content first
    const hoveredCard = educational?.content?.find(c => c.pattern_id === hoveredPatternId);
    let bracket = hoveredCard?.visualization?.bracket_range;

    // Fallback: find bracket range from pattern data
    if (!bracket && analysis.primary.patterns) {
      const hoveredPattern = analysis.primary.patterns.find(p => p.pattern_id === hoveredPatternId);
      if (hoveredPattern) {
        bracket = { start: hoveredPattern.start, end: hoveredPattern.end };
      }
    }

    if (!bracket) return [];

    const { start, end } = bracket;
    const indices: number[] = [];
    for (let i = start; i <= end; i++) {
      indices.push(i);
    }
    return indices;
  };

  // Big play: Get the hovered bracket range for selective bracket highlighting
  const getHoveredBracketRange = () => {
    if (!hoveredPatternId) return null;

    // Try educational content first
    const hoveredCard = educational?.content?.find(c => c.pattern_id === hoveredPatternId);
    if (hoveredCard?.visualization?.bracket_range) {
      return hoveredCard.visualization.bracket_range;
    }

    // Fallback: use pattern data
    if (analysis.primary.patterns) {
      const hoveredPattern = analysis.primary.patterns.find(p => p.pattern_id === hoveredPatternId);
      if (hoveredPattern) {
        return { start: hoveredPattern.start, end: hoveredPattern.end };
      }
    }

    return null;
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

      {/* Pattern Analysis - unified view combining educational and technical information */}
      {analysis.primary.patterns && analysis.primary.patterns.length > 0 && showEducational && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">
            Pattern Analysis ({analysis.primary.patterns.length})
          </h3>
          {analysis.primary.patterns.map((pattern, idx) => {
            // Match pattern with educational content and explanation
            const eduContent = educational?.content?.find(
              card => card.pattern_id === pattern.pattern_id
            );
            const explanation = eduContent
              ? educational?.explanations?.[pattern.pattern_id]
              : undefined;

            return (
              <EnhancedPatternCard
                key={pattern.pattern_id || idx}
                pattern={pattern}
                educationalContent={eduContent}
                explanation={explanation}
                onHover={setHoveredPatternId}
                onLeave={() => setHoveredPatternId(null)}
              />
            );
          })}
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
