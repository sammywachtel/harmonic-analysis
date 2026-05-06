// Smoke test for HeroKeyCard. Validates the basics that the Tab 1/2 hero
// reads correctly: serif tonic, mode word, key-signature glyph, confidence %.

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import HeroKeyCard from '../HeroKeyCard';

describe('HeroKeyCard', () => {
  it('renders tonic, mode, and confidence percentage', () => {
    render(
      <HeroKeyCard
        tonic="C"
        mode="major"
        keySignature="0 sharps"
        confidence={0.92}
      />,
    );

    expect(screen.getByTestId('hero-tonic')).toHaveTextContent('C');
    expect(screen.getByText('major')).toBeInTheDocument();
    expect(screen.getByText(/Confidence 92\.0%/)).toBeInTheDocument();
  });

  it('renders alt-reading callout when provided', () => {
    render(
      <HeroKeyCard
        tonic="A"
        mode="minor"
        keySignature="0 sharps"
        confidence={0.78}
        altReading="F♯ Dorian"
      />,
    );

    expect(screen.getByText('also reads as')).toBeInTheDocument();
    expect(screen.getByText('F♯ Dorian')).toBeInTheDocument();
  });

  it('emits the hero-key-card test id for downstream selectors', () => {
    render(
      <HeroKeyCard
        tonic="G"
        mode="mixolydian"
        keySignature="1 sharp"
        confidence={0.65}
      />,
    );

    expect(screen.getByTestId('hero-key-card')).toBeInTheDocument();
  });

  it('labels minor modes correctly in the meta line', () => {
    render(
      <HeroKeyCard tonic="A" mode="aeolian" keySignature="0 sharps" confidence={0.5} />,
    );
    expect(screen.getByText(/minor-mode tonic/i)).toBeInTheDocument();
  });
});
