// Test suite for ChordProgressionVisual component.
// Validates color stripes (cards keep a white body; the function role is
// communicated via a top-stripe div), bracket rendering on a CSS grid, and
// hover interactions.

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChordProgressionVisual } from '../ChordProgressionVisual';

const buildPatternViz = (
  chordColors: string[],
  bracketRange: { start: number; end: number },
  labels: string[] = ['Pattern'],
) => ([{ chordColors, bracketRange, labels }]);

/** Helper: get the function color stripe inside a chord card.
 *  Cards render a 4px stripe at the top with the function background class. */
const getStripe = (card: Element): Element | null =>
  card.querySelector('div.absolute.top-0');

describe('ChordProgressionVisual', () => {
  it('renders all chords in the progression', () => {
    const chords = ['Dm', 'G7', 'C'];
    render(<ChordProgressionVisual chords={chords} />);

    expect(screen.getByText('Dm')).toBeInTheDocument();
    expect(screen.getByText('G7')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();
  });

  it('applies correct stripe color classes from patternVisualizations', () => {
    const chords = ['Dm', 'G7', 'C'];

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        patternVisualizations={buildPatternViz(['PD', 'D', 'T'], { start: 0, end: 2 })}
      />
    );

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes).toHaveLength(3);

    expect(getStripe(chordBoxes[0])).toHaveClass('bg-indigo-500');  // PD
    expect(getStripe(chordBoxes[1])).toHaveClass('bg-amber-500');   // D
    expect(getStripe(chordBoxes[2])).toHaveClass('bg-emerald-500'); // T
  });

  it('renders pattern bracket when patternVisualizations is provided', () => {
    const chords = ['Dm', 'G7', 'C'];

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        patternVisualizations={buildPatternViz(['PD', 'D', 'T'], { start: 1, end: 2 })}
      />
    );

    const svgElement = container.querySelector('svg');
    expect(svgElement).toBeInTheDocument();

    const patternTexts = screen.getAllByText('Pattern');
    expect(patternTexts.length).toBeGreaterThanOrEqual(1);
  });

  it('highlights chords when highlightedChords prop is provided', () => {
    const chords = ['F', 'G7', 'C'];

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        patternVisualizations={buildPatternViz(['PD', 'D', 'T'], { start: 0, end: 2 })}
        highlightedChords={[1, 2]}
      />
    );

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes[0]).not.toHaveClass('ring-2');
    expect(chordBoxes[1]).toHaveClass('ring-2');
    expect(chordBoxes[2]).toHaveClass('ring-2');
  });

  it('renders color legend with all function labels when patterns have colors', () => {
    const chords = ['G7', 'C'];
    render(
      <ChordProgressionVisual
        chords={chords}
        patternVisualizations={buildPatternViz(['D', 'T'], { start: 0, end: 1 })}
      />
    );

    expect(screen.getByText('Color guide')).toBeInTheDocument();
    expect(screen.getByText('Setup')).toBeInTheDocument();
    // "Pattern" appears in the legend; bracket label uses the same word.
    const patternMatches = screen.getAllByText('Pattern');
    expect(patternMatches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Resolution')).toBeInTheDocument();
  });

  it('provides proper ARIA labels for chord boxes', () => {
    const chords = ['G7', 'C'];

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        patternVisualizations={buildPatternViz(['D', 'T'], { start: 0, end: 1 })}
      />
    );

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes[0]).toHaveAttribute('aria-label', 'G7 - Dominant Function');
    expect(chordBoxes[1]).toHaveAttribute('aria-label', 'C - Tonic Function');
  });

  it('handles empty chord array gracefully', () => {
    const { container } = render(<ChordProgressionVisual chords={[]} />);
    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes).toHaveLength(0);
  });

  it('renders neutral cards (no function color) when patternVisualizations is omitted', () => {
    const chords = ['Dm', 'G7', 'C'];
    const { container } = render(<ChordProgressionVisual chords={chords} />);

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    // Cards are white-bodied; the stripe falls back to slate when there's no
    // function info. None of the function color classes should leak in.
    expect(getStripe(chordBoxes[0])).toHaveClass('bg-slate-200');
    expect(getStripe(chordBoxes[0])).not.toHaveClass('bg-indigo-500');
    expect(getStripe(chordBoxes[0])).not.toHaveClass('bg-amber-500');
    expect(getStripe(chordBoxes[0])).not.toHaveClass('bg-emerald-500');
  });

  it('displays PAC example correctly with proper stripe colors and bracket', () => {
    const chords = ['G7', 'C'];

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        patternVisualizations={buildPatternViz(['D', 'T'], { start: 0, end: 1 })}
      />
    );

    expect(screen.getByText('G7')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(getStripe(chordBoxes[0])).toHaveClass('bg-amber-500');    // G7 = Dominant
    expect(getStripe(chordBoxes[1])).toHaveClass('bg-emerald-500');  // C = Tonic

    const svgElement = container.querySelector('svg');
    expect(svgElement).toBeInTheDocument();
  });
});
