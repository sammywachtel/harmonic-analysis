// Test suite for ChordProgressionVisual component
// Validates color coding, bracket rendering, and hover interactions

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChordProgressionVisual } from '../ChordProgressionVisual';

describe('ChordProgressionVisual', () => {
  // Opening move: Test basic rendering
  it('renders all chords in the progression', () => {
    const chords = ['Dm', 'G7', 'C'];
    render(<ChordProgressionVisual chords={chords} />);

    // Main play: Verify each chord is rendered
    expect(screen.getByText('Dm')).toBeInTheDocument();
    expect(screen.getByText('G7')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();
  });

  // Big play: Test color coding functionality
  it('applies correct color classes based on chord_colors prop', () => {
    const chords = ['Dm', 'G7', 'C'];
    const chordColors = ['PD', 'D', 'T'];
    const bracketRange = { start: 0, end: 2 }; // All chords in pattern

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        chordColors={chordColors}
        bracketRange={bracketRange}
      />
    );

    // Time to tackle the tricky bit: Find chord boxes and verify colors
    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes).toHaveLength(3);

    // Verify color classes
    expect(chordBoxes[0]).toHaveClass('bg-blue-500'); // PD = blue
    expect(chordBoxes[1]).toHaveClass('bg-orange-500'); // D = orange
    expect(chordBoxes[2]).toHaveClass('bg-green-500'); // T = green
  });

  // Victory lap: Test bracket rendering
  it('renders pattern bracket when bracketRange is provided', () => {
    const chords = ['Dm', 'G7', 'C'];
    const bracketRange = { start: 1, end: 2 };

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        chordColors={['PD', 'D', 'T']}
        bracketRange={bracketRange}
      />
    );

    // Here's where we check for the SVG bracket
    const svgElement = container.querySelector('svg');
    expect(svgElement).toBeInTheDocument();

    // Pattern text is now a span element outside the SVG (to avoid stretching)
    // Use screen.getAllByText since "Pattern" also appears in the legend
    const patternTexts = screen.getAllByText('Pattern');
    expect(patternTexts.length).toBeGreaterThanOrEqual(2); // One in bracket, one in legend
  });

  // Main play: Test highlight functionality
  it('highlights chords when highlightedChords prop is provided', () => {
    const chords = ['F', 'G7', 'C'];
    const chordColors = ['PD', 'D', 'T'];
    const bracketRange = { start: 0, end: 2 }; // All chords in bracket
    const highlightedChords = [1, 2]; // Highlight G7 and C

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        chordColors={chordColors}
        bracketRange={bracketRange}
        highlightedChords={highlightedChords}
      />
    );

    const chordBoxes = container.querySelectorAll('[role="listitem"]');

    // Verify ring effect on highlighted chords
    expect(chordBoxes[0]).not.toHaveClass('ring-4');
    expect(chordBoxes[1]).toHaveClass('ring-4');
    expect(chordBoxes[2]).toHaveClass('ring-4');
  });

  // Big play: Test color legend rendering
  it('renders color legend with all function labels', () => {
    const chords = ['G7', 'C'];
    render(<ChordProgressionVisual chords={chords} />);

    // Verify legend labels
    expect(screen.getByText('Color Guide:')).toBeInTheDocument();
    expect(screen.getByText('Setup')).toBeInTheDocument();
    expect(screen.getByText('Pattern')).toBeInTheDocument();
    expect(screen.getByText('Resolution')).toBeInTheDocument();
  });

  // Time to tackle the tricky bit: Test accessibility
  it('provides proper ARIA labels for chord boxes', () => {
    const chords = ['G7', 'C'];
    const chordColors = ['D', 'T'];
    const bracketRange = { start: 0, end: 1 };

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        chordColors={chordColors}
        bracketRange={bracketRange}
      />
    );

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes[0]).toHaveAttribute('aria-label', 'G7 - Dominant Function');
    expect(chordBoxes[1]).toHaveAttribute('aria-label', 'C - Tonic Function');
  });

  // Victory lap: Test edge cases
  it('handles empty chord array gracefully', () => {
    const { container } = render(<ChordProgressionVisual chords={[]} />);
    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes).toHaveLength(0);
  });

  it('renders chords without colors when chordColors is not provided', () => {
    const chords = ['Dm', 'G7', 'C'];
    const { container } = render(<ChordProgressionVisual chords={chords} />);

    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    // Here's where we check fallback styling kicks in
    expect(chordBoxes[0]).toHaveClass('bg-slate-200');
  });

  // Main play: Test PAC example from acceptance criteria
  it('displays PAC example correctly with proper colors and bracket', () => {
    const chords = ['G7', 'C'];
    const chordColors = ['D', 'T'];  // Dominant, Tonic
    const bracketRange = { start: 0, end: 1 };

    const { container } = render(
      <ChordProgressionVisual
        chords={chords}
        chordColors={chordColors}
        bracketRange={bracketRange}
      />
    );

    // Verify all chords rendered
    expect(screen.getByText('G7')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();

    // Verify colors match harmonic function (orange for G7/Dominant, green for C/Tonic)
    const chordBoxes = container.querySelectorAll('[role="listitem"]');
    expect(chordBoxes[0]).toHaveClass('bg-orange-500');  // G7 = Dominant
    expect(chordBoxes[1]).toHaveClass('bg-green-500');   // C = Tonic

    // Verify bracket under both chords
    const svgElement = container.querySelector('svg');
    expect(svgElement).toBeInTheDocument();

    // Pattern text is now a span element outside the SVG
    const patternTexts = screen.getAllByText('Pattern');
    expect(patternTexts.length).toBeGreaterThanOrEqual(2); // One in bracket, one in legend
  });
});
