// Top-level results display. The big architectural moves are unchanged from
// the old chip-heavy version — we still derive bracket ranges from
// patterns/educational content, still wire hover handlers from pattern cards
// down to the chord viz — but the chrome is now SectionCard + HeroKeyCard +
// RomanScoreLine + ConfidenceBar atoms instead of bespoke divs everywhere.
//
// The multi-profile, modal, and chromatic surfaces all stay; they just live
// inside reskinned SectionCards.

import { useState } from 'react';
import type { AnalysisResponse } from '../types/analysis';
import { EnhancedPatternCard } from './EnhancedPatternCard';
import { ChordProgressionVisual } from './ChordProgressionVisual';
import StyleBadge from './StyleBadge';
import StyleAnalysisSection from './StyleAnalysisSection';
import HeroKeyCard from './HeroKeyCard';
import RomanScoreLine from './RomanScoreLine';
import SectionCard from './ui/SectionCard';
import ConfidenceBar from './ui/ConfidenceBar';
import Tag from './ui/Tag';
import Eyebrow from './ui/Eyebrow';
import { getStyleConfig } from '../utils/styleConfig';
import '../styles/multi-profile.css';

interface AnalysisResultsProps {
  results: AnalysisResponse;
  showEducational?: boolean;
  chords?: string[];
}

// Split "C major" or "G mixolydian" into a tonic + mode pair. Falls back to
// using the whole string as the tonic when we can't parse — better to over-show
// than to silently drop information.
const splitKeyAndMode = (
  keySignature: string,
  modeOverride?: string | null,
): { tonic: string; mode: string } => {
  const trimmed = keySignature.trim();
  const match = trimmed.match(/^([A-G][#b♯♭]?)\s+(.+)$/);
  if (match) {
    return { tonic: match[1].replace('#', '♯').replace('b', '♭'), mode: modeOverride ?? match[2] };
  }
  return { tonic: trimmed, mode: modeOverride ?? '' };
};

// Parse a dense engine-output string into structured segments. The library
// often returns a single string like:
//   "Detected patterns: Mixolydian ♭VII-III; Progression: i → V7 → i; …"
// which is hostile to scan as one paragraph. We split on "; " and, for each
// segment, peel off the "Label: body" prefix when present so the renderer can
// give labels their own typographic weight.
type EngineNote =
  | { kind: 'labeled'; label: string; body: string }
  | { kind: 'free'; body: string };

const parseEngineText = (text: string): EngineNote[] => {
  return text
    .split(/;\s*/)
    .map((seg) => seg.trim())
    .filter(Boolean)
    .map<EngineNote>((seg) => {
      // Peel "Label: body". We require the label to be short-ish and start
      // with a letter so we don't misfire on prose with stray colons (URLs,
      // ratios, time-of-day, etc.).
      const colonIdx = seg.indexOf(':');
      if (colonIdx > 0 && colonIdx <= 32) {
        const label = seg.slice(0, colonIdx).trim();
        const body = seg.slice(colonIdx + 1).trim();
        if (/^[A-Za-z][A-Za-z0-9 ]*$/.test(label) && body) {
          return { kind: 'labeled', label, body };
        }
      }
      return { kind: 'free', body: seg };
    });
};

// Detect chord-progression-y bodies. Either explicit arrows ("i → V7 → I") or
// hyphen-chains of Roman/chord tokens ("i-V7-i"). The latter only matches when
// the whole string is dashes-and-tokens — we don't want to format prose
// containing one stray hyphen as a progression.
const isProgressionBody = (body: string): boolean => {
  if (/[→]/.test(body)) return true;
  return /^[A-Ga-gIVXivx#♭♯b°ø+♮0-9maj]+(?:-[A-Ga-gIVXivx#♭♯b°ø+♮0-9maj]+){2,}$/i.test(
    body.trim(),
  );
};

// Render a chord/Roman progression with the editorial type treatment: serif
// italic tokens, slate dividers, wraps cleanly when wide.
const renderProgressionBody = (body: string) => {
  // Normalize separators: turn hyphens into arrows for visual consistency.
  const tokens = body
    .split(/(?:\s*→\s*|-)/)
    .map((t) => t.trim())
    .filter(Boolean);
  return (
    <span className="inline-flex flex-wrap items-baseline gap-x-1.5 gap-y-1">
      {tokens.map((tok, i) => (
        <span key={i} className="inline-flex items-baseline gap-1.5">
          <span className="font-serif italic text-base text-primary-800 font-semibold leading-none">
            {tok}
          </span>
          {i < tokens.length - 1 && (
            <span className="text-slate-300 text-sm leading-none" aria-hidden="true">→</span>
          )}
        </span>
      ))}
    </span>
  );
};

// Renders a parsed engine-text payload as a labeled list. Labels sit in
// eyebrow style; bodies render as either a chord progression (serif tokens)
// or plain text. Free segments (no label) come through as quiet italic notes.
const EngineNotes = ({ text }: { text: string }) => {
  const segments = parseEngineText(text);
  if (segments.length === 0) return null;
  return (
    <dl className="space-y-2.5">
      {segments.map((seg, i) =>
        seg.kind === 'labeled' ? (
          <div key={i} className="grid grid-cols-1 sm:grid-cols-[10rem_1fr] gap-x-4 gap-y-0.5">
            <dt className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 sm:pt-1">
              {seg.label}
            </dt>
            <dd className="text-sm text-slate-700 leading-relaxed">
              {isProgressionBody(seg.body) ? renderProgressionBody(seg.body) : seg.body}
            </dd>
          </div>
        ) : (
          <div key={i} className="text-xs italic text-slate-500 leading-relaxed sm:ml-[10.75rem]">
            {seg.body}
          </div>
        ),
      )}
    </dl>
  );
};

const AnalysisResults = ({ results, showEducational = true, chords = [] }: AnalysisResultsProps) => {
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [hoveredPatternId, setHoveredPatternId] = useState<string | null>(null);

  const { analysis, enhanced_summaries, educational } = results;
  const hasAlternatives = analysis.alternatives && analysis.alternatives.length > 0;

  // ── Bracket-overlay machinery (unchanged from previous implementation) ───
  // Group every pattern by bracket range, merge labels, sort left-to-right.
  const getAllPatternVisualizations = () => {
    const groups: Array<{
      chordColors?: string[];
      bracketRange: { start: number; end: number };
      labels: string[];
    }> = [];

    if (analysis.primary.patterns && analysis.primary.patterns.length > 0) {
      analysis.primary.patterns.forEach((pattern) => {
        const eduContent = educational?.content?.find(
          (card) => card.pattern_id === pattern.pattern_id,
        );
        const bracket = eduContent?.visualization?.bracket_range
          ? eduContent.visualization.bracket_range
          : { start: pattern.start, end: pattern.end };
        const label = eduContent?.title || pattern.name;
        const chordColors = eduContent?.visualization?.chord_colors;
        const existing = groups.find(
          (g) => g.bracketRange.start === bracket.start && g.bracketRange.end === bracket.end,
        );
        if (existing) {
          existing.labels.push(label);
        } else {
          groups.push({ chordColors, bracketRange: bracket, labels: [label] });
        }
      });
    }
    return groups.sort((a, b) => a.bracketRange.start - b.bracketRange.start);
  };

  const allPatternVisualizations = getAllPatternVisualizations();

  // Hover → highlight: which chord indices belong to the hovered pattern's bracket.
  const getHighlightedChords = (): number[] => {
    if (!hoveredPatternId) return [];
    const card = educational?.content?.find((c) => c.pattern_id === hoveredPatternId);
    let bracket = card?.visualization?.bracket_range;
    if (!bracket && analysis.primary.patterns) {
      const p = analysis.primary.patterns.find((p) => p.pattern_id === hoveredPatternId);
      if (p) bracket = { start: p.start, end: p.end };
    }
    if (!bracket) return [];
    const out: number[] = [];
    for (let i = bracket.start; i <= bracket.end; i++) out.push(i);
    return out;
  };

  const getHoveredBracketRange = () => {
    if (!hoveredPatternId) return null;
    const card = educational?.content?.find((c) => c.pattern_id === hoveredPatternId);
    if (card?.visualization?.bracket_range) return card.visualization.bracket_range;
    if (analysis.primary.patterns) {
      const p = analysis.primary.patterns.find((p) => p.pattern_id === hoveredPatternId);
      if (p) return { start: p.start, end: p.end };
    }
    return null;
  };

  // ── Hero card data ───────────────────────────────────────────────────────
  const { tonic, mode } = splitKeyAndMode(
    analysis.primary.key_signature,
    analysis.primary.mode,
  );

  const typeTone =
    analysis.primary.type === 'modal'
      ? 'indigo'
      : analysis.primary.type === 'chromatic'
        ? 'amber'
        : 'primary';

  return (
    <div className="space-y-8">
      {/* Analysis Summary banner — quiet slate-toned eyebrow + body. */}
      <SectionCard eyebrow="Summary" title="Analysis">
        <p className="text-sm text-slate-700 leading-relaxed">{results.summary}</p>
      </SectionCard>

      {/* Chord progression with bracket overlays. The bracket math is
          unchanged; we just wrap the existing component in SectionCard chrome. */}
      {chords.length > 0 && (
        <SectionCard
          eyebrow="Progression"
          title="Chord progression"
          subtitle={`${chords.length} ${chords.length === 1 ? 'chord' : 'chords'} with detected pattern overlays`}
        >
          <ChordProgressionVisual
            chords={chords}
            patternVisualizations={allPatternVisualizations}
            highlightedChords={getHighlightedChords()}
            hoveredBracketRange={getHoveredBracketRange()}
          />
        </SectionCard>
      )}

      {/* Hero key card + Roman score-line. The dominant-style and analysis-type
          tags carry the multi-profile context that used to live in the header. */}
      <div className="space-y-5">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <Eyebrow tone="primary">Detected key</Eyebrow>
          <div className="flex items-center gap-2">
            {analysis.primary.dominant_style && (
              <StyleBadge style={analysis.primary.dominant_style} data-testid="dominant-style-badge" />
            )}
            {!analysis.primary.dominant_style && analysis.primary.type && (
              <Tag tone={typeTone}>
                {analysis.primary.type.charAt(0).toUpperCase() + analysis.primary.type.slice(1)}
              </Tag>
            )}
          </div>
        </div>

        <HeroKeyCard
          tonic={tonic}
          mode={mode}
          keySignature={analysis.primary.key_signature}
          confidence={analysis.primary.confidence}
        />

        {analysis.primary.roman_numerals.length > 0 && (
          <RomanScoreLine
            numerals={analysis.primary.roman_numerals}
            chords={chords.length === analysis.primary.roman_numerals.length ? chords : undefined}
            label="Roman numerals · the chord roadmap"
          />
        )}
      </div>

      {/* Confidence breakdown — three quick bars when the engine returns them. */}
      {(analysis.primary.functional_confidence !== undefined ||
        analysis.primary.modal_confidence !== undefined ||
        analysis.primary.chromatic_confidence !== undefined) && (
        <SectionCard eyebrow="Style confidence" title="How each lens reads it">
          <div className="space-y-3 max-w-md">
            {analysis.primary.functional_confidence !== undefined && (
              <ConfidenceBar
                value={analysis.primary.functional_confidence}
                color="primary"
                label="Functional"
                size="md"
                valueFormat={(v) => `${(v * 100).toFixed(0)}%`}
              />
            )}
            {analysis.primary.modal_confidence !== undefined && (
              <ConfidenceBar
                value={analysis.primary.modal_confidence}
                color="indigo"
                label="Modal"
                size="md"
                valueFormat={(v) => `${(v * 100).toFixed(0)}%`}
              />
            )}
            {analysis.primary.chromatic_confidence !== undefined && (
              <ConfidenceBar
                value={analysis.primary.chromatic_confidence}
                color="amber"
                label="Chromatic"
                size="md"
                valueFormat={(v) => `${(v * 100).toFixed(0)}%`}
              />
            )}
          </div>
        </SectionCard>
      )}

      {/* Multi-profile per-style confidence — preserves the existing animated
          bar tooling while wrapping it in SectionCard chrome. The legacy CSS
          classes (.confidence-bar-container, .bar-classical, etc.) keep
          working; tests still pass. */}
      {analysis.primary.style_confidence && Object.keys(analysis.primary.style_confidence).length > 0 && (
        <SectionCard
          eyebrow="Multi-profile"
          title="Style confidence"
          subtitle="How strongly the progression typifies each musical style"
          className="style-confidence-section"
        >
          <div data-testid="style-confidence-section">
            {Object.entries(analysis.primary.style_confidence)
              .sort(([, a], [, b]) => b - a)
              .map(([style, confidence]) => {
                const config = getStyleConfig(style);
                const barClass = `bar-${style.toLowerCase()}`;
                return (
                  <div
                    key={style}
                    className="confidence-bar-container"
                    data-testid={`style-confidence-${style.toLowerCase()}`}
                  >
                    <span className="confidence-bar-label">
                      <span className="mr-1" aria-hidden="true">{config.icon}</span>
                      {config.label}
                    </span>
                    <div
                      className="confidence-bar-track"
                      role="progressbar"
                      aria-valuenow={confidence * 100}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${config.label} confidence: ${(confidence * 100).toFixed(0)}%`}
                    >
                      <div
                        className={`confidence-bar-fill ${barClass} h-full rounded`}
                        style={{ '--bar-width': `${confidence * 100}%` } as React.CSSProperties}
                      />
                    </div>
                    <span className="confidence-bar-percentage">
                      {(confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                );
              })}
          </div>
        </SectionCard>
      )}

      {/* Reasoning, interpretation, cadence prose. The engine emits these as
          dense semicolon-glued paragraphs ("Detected patterns: …; Progression:
          i → V7 → i; Cadence outline: …; Modal accents: …"). EngineNotes
          parses each into label + body and gives chord progressions the serif
          treatment so they're scannable instead of a wall of glyphs. */}
      {(analysis.primary.reasoning ||
        analysis.primary.interpretation ||
        analysis.primary.cadence_detection) && (
        <SectionCard eyebrow="Notes" title="What the engine is hearing">
          <div className="space-y-5">
            {analysis.primary.reasoning && (
              <section>
                <Eyebrow tone="primary" className="mb-2">Reasoning</Eyebrow>
                <EngineNotes text={analysis.primary.reasoning} />
              </section>
            )}
            {analysis.primary.interpretation && (
              <section>
                <Eyebrow tone="primary" className="mb-2">Interpretation</Eyebrow>
                <EngineNotes text={analysis.primary.interpretation} />
              </section>
            )}
            {analysis.primary.cadence_detection && (
              <section>
                <Eyebrow tone="primary" className="mb-2">Cadence</Eyebrow>
                <EngineNotes text={analysis.primary.cadence_detection} />
              </section>
            )}
          </div>
        </SectionCard>
      )}

      {/* Pattern analysis — list of restyled cards. Hover handlers still
          drive bracket highlighting in ChordProgressionVisual above. */}
      {analysis.primary.patterns && analysis.primary.patterns.length > 0 && showEducational && (
        <SectionCard
          eyebrow="Patterns"
          title={`Pattern analysis · ${analysis.primary.patterns.length}`}
          subtitle="Hover a card to see which chords participate"
        >
          <div className="space-y-3">
            {analysis.primary.patterns.map((pattern, idx) => {
              const eduContent = educational?.content?.find(
                (card) => card.pattern_id === pattern.pattern_id,
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
        </SectionCard>
      )}

      {/* Multi-profile per-style breakdown disclosure (StyleAnalysisSection
          already implements the expand/collapse). */}
      {analysis.primary.style_analysis && Object.keys(analysis.primary.style_analysis).length > 0 && (
        <StyleAnalysisSection
          styleAnalysis={analysis.primary.style_analysis}
          dominantStyle={analysis.primary.dominant_style}
        />
      )}

      {/* Modal characteristics — bullet list, indigo eyebrow per design. */}
      {analysis.primary.modal_characteristics && analysis.primary.modal_characteristics.length > 0 && (
        <SectionCard eyebrow="Modal" title="Modal characteristics">
          <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
            {analysis.primary.modal_characteristics.map((char, idx) => (
              <li key={idx}>{char}</li>
            ))}
          </ul>
        </SectionCard>
      )}

      {/* Modal evidence — narrative rows with strength sparks. */}
      {analysis.primary.modal_evidence && analysis.primary.modal_evidence.length > 0 && (
        <SectionCard eyebrow="Modal" title="Modal evidence">
          <div className="space-y-3">
            {analysis.primary.modal_evidence.map((evidence, idx) => (
              <div key={idx} className="text-sm text-slate-700 leading-relaxed">
                <span className="font-semibold text-slate-900">{evidence.type}.</span>{' '}
                {evidence.description}{' '}
                <span className="text-slate-500 font-mono text-xs tabular-nums">
                  ({(evidence.strength * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Chromatic elements — non-diatonic chord callouts. */}
      {analysis.primary.chromatic_elements && analysis.primary.chromatic_elements.length > 0 && (
        <SectionCard eyebrow="Chromatic" title="Chromatic elements">
          <ul className="list-disc list-inside space-y-1.5 text-sm text-slate-700">
            {analysis.primary.chromatic_elements.map((element, idx) => (
              <li key={idx}>
                <span className="font-mono font-semibold text-slate-900">{element.symbol}</span>
                {element.type && <span className="text-slate-500"> · {element.type}</span>}
                {element.resolution && <span className="text-slate-500"> → {element.resolution}</span>}
                {element.strength != null && (
                  <span className="ml-2 text-xs font-mono tabular-nums text-slate-500">
                    [{(element.strength * 100).toFixed(0)}%]
                  </span>
                )}
                {element.explanation && <span className="text-slate-600"> — {element.explanation}</span>}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {/* Patterns detected (engine-side summary string list). */}
      {enhanced_summaries?.patterns_detected && enhanced_summaries.patterns_detected.length > 0 && (
        <SectionCard eyebrow="Engine summary" title="Patterns detected">
          <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
            {enhanced_summaries.patterns_detected.map((pattern, idx) => (
              <li key={idx}>{pattern}</li>
            ))}
          </ul>
        </SectionCard>
      )}

      {/* Alternative interpretations — disclosure pattern. */}
      {hasAlternatives && (
        <SectionCard
          eyebrow="Alternatives"
          title={`Other readings · ${analysis.alternatives!.length}`}
          action={
            <button
              type="button"
              onClick={() => setShowAlternatives(!showAlternatives)}
              aria-expanded={showAlternatives}
              className="text-sm text-primary-700 hover:text-primary-900 font-medium flex items-center gap-1"
            >
              {showAlternatives ? 'Hide' : 'Show'}
              <svg
                className={`w-4 h-4 transition-transform ${showAlternatives ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          }
        >
          {showAlternatives ? (
            <div className="space-y-4">
              {analysis.alternatives!.map((alt, idx) => {
                const altSplit = splitKeyAndMode(alt.key_signature, alt.mode);
                return (
                  <div
                    key={idx}
                    className="border border-slate-200 rounded-xl p-4 bg-slate-50/40"
                  >
                    <div className="flex items-baseline justify-between gap-3 mb-2 flex-wrap">
                      <div className="font-serif text-2xl text-slate-900 tracking-tight">
                        {altSplit.tonic}{' '}
                        {altSplit.mode && (
                          <span className="text-slate-400 italic font-light text-lg">{altSplit.mode}</span>
                        )}
                      </div>
                      <span className="text-xs font-mono tabular-nums text-slate-500">
                        Confidence {(alt.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <RomanScoreLine numerals={alt.roman_numerals} size="md" />
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Other readings the engine considered — open to compare.
            </p>
          )}
        </SectionCard>
      )}
    </div>
  );
};

export default AnalysisResults;
