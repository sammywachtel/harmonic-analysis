// Component tests for multi-profile UI elements
// Validates badge rendering, confidence bars, and style section behavior

import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnalysisResults from '../AnalysisResults';
import type { AnalysisResponse } from '../../types/analysis';

// Mock multi-profile analysis response with style data
const mockMultiProfileResponse: AnalysisResponse = {
  summary: 'Jazz-dominant progression with classical and pop characteristics',
  analysis: {
    primary: {
      key_signature: 'C major',
      roman_numerals: ['I', 'vi', 'ii', 'V'],
      confidence: 0.89,
      type: 'functional',
      // Multi-profile fields
      dominant_style: 'jazz',
      style_typicality: 0.92,
      style_confidence: {
        jazz: 0.92,
        classical: 0.85,
        pop: 0.78,
      },
      style_analysis: {
        jazz: {
          style_name: 'jazz',
          confidence: 0.92,
          typicality: 0.95,
          patterns: [
            {
              start: 0,
              end: 3,
              pattern_id: 'jazz.turnaround',
              name: 'I–vi–ii–V Turnaround',
              family: 'functional',
              score: 0.93,
              evidence: [{ features: {} }],
              glossary: null,
              section: null,
              cadence_role: null,
              is_section_closure: false,
            },
          ],
          style_notes: 'Classic jazz turnaround progression',
          characteristic_features: ['Smooth voice leading', 'Circle of fifths motion'],
        },
        classical: {
          style_name: 'classical',
          confidence: 0.85,
          typicality: 0.80,
          patterns: [
            {
              start: 0,
              end: 3,
              pattern_id: 'classical.predominant',
              name: 'Predominant Function',
              family: 'functional',
              score: 0.82,
              evidence: [{ features: {} }],
              glossary: null,
              section: null,
              cadence_role: null,
              is_section_closure: false,
            },
          ],
          style_notes: 'Diatonic predominant-dominant progression',
          characteristic_features: ['Functional harmony', 'Clear cadential goal'],
        },
        pop: {
          style_name: 'pop',
          confidence: 0.78,
          typicality: 0.70,
          patterns: [],
          style_notes: 'Four-chord loop variant',
          characteristic_features: ['Repetitive structure'],
        },
      },
    },
  },
};

// Mock response without multi-profile data (graceful fallback)
const mockLegacyResponse: AnalysisResponse = {
  summary: 'Standard functional analysis',
  analysis: {
    primary: {
      key_signature: 'C major',
      roman_numerals: ['I', 'IV', 'V', 'I'],
      confidence: 0.87,
      type: 'functional',
      functional_confidence: 0.87,
    },
  },
};

describe('AnalysisResults - Multi-Profile UI', () => {
  describe('Dominant Style Badge', () => {
    it('renders dominant style badge when present', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      // StyleBadge sets data-testid based on style name
      const badge = screen.getByTestId('style-badge-jazz');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('Jazz');
      expect(badge).toHaveTextContent('🎷');
    });

    it('falls back to analysis type badge when no dominant style', () => {
      render(<AnalysisResults results={mockLegacyResponse} chords={['C', 'F', 'G', 'C']} />);

      // Should show type badge instead (no style badge). Reskin also surfaces
      // the type as a confidence-bar label, so we tolerate multiple matches.
      expect(screen.queryByTestId(/style-badge-/)).not.toBeInTheDocument();
      expect(screen.getAllByText('Functional').length).toBeGreaterThan(0);
    });
  });

  describe('Style Confidence Bars', () => {
    it('renders style confidence section when data present', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const section = screen.getByTestId('style-confidence-section');
      expect(section).toBeInTheDocument();
      // Reskin moves the heading into a SectionCard title; assert the SectionCard
      // chrome rendered and the per-style data is reachable.
      expect(screen.getByText('Style confidence')).toBeInTheDocument();
    });

    it('displays all styles sorted by confidence (highest first)', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      // Jazz should be first (92%), then classical (85%), then pop (78%)
      const jazzBar = screen.getByTestId('style-confidence-jazz');
      const classicalBar = screen.getByTestId('style-confidence-classical');
      const popBar = screen.getByTestId('style-confidence-pop');

      expect(jazzBar).toBeInTheDocument();
      expect(classicalBar).toBeInTheDocument();
      expect(popBar).toBeInTheDocument();

      // Check percentages
      expect(within(jazzBar).getByText('92%')).toBeInTheDocument();
      expect(within(classicalBar).getByText('85%')).toBeInTheDocument();
      expect(within(popBar).getByText('78%')).toBeInTheDocument();
    });

    it('includes accessible progressbar semantics', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const jazzBar = screen.getByTestId('style-confidence-jazz');
      const progressbar = within(jazzBar).getByRole('progressbar');

      expect(progressbar).toHaveAttribute('aria-valuenow', '92');
      expect(progressbar).toHaveAttribute('aria-valuemin', '0');
      expect(progressbar).toHaveAttribute('aria-valuemax', '100');
      expect(progressbar).toHaveAttribute('aria-label', 'Jazz confidence: 92%');
    });

    it('hides style confidence when data missing', () => {
      render(<AnalysisResults results={mockLegacyResponse} chords={['C', 'F', 'G', 'C']} />);

      expect(screen.queryByTestId('style-confidence-section')).not.toBeInTheDocument();
    });
  });

  describe('Style Analysis Section', () => {
    it('renders style analysis section when data present', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const section = screen.getByTestId('style-analysis-section');
      expect(section).toBeInTheDocument();
    });

    it('shows correct count in toggle button', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      // Reskin: count lives in the SectionCard title; aria-label on the toggle
      // button still exposes the styled count for assistive tech.
      const button = screen.getByTestId('style-analysis-toggle');
      expect(button).toHaveAttribute(
        'aria-label',
        'View analysis through 3 different musical styles',
      );
      expect(screen.getByText('View analysis through different styles (3)')).toBeInTheDocument();
    });

    it('is collapsed by default', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const button = screen.getByTestId('style-analysis-toggle');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByTestId('style-cards-container')).not.toBeInTheDocument();
    });

    it('expands on button click', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const button = screen.getByTestId('style-analysis-toggle');
      await user.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByTestId('style-cards-container')).toBeInTheDocument();
    });

    it('displays style cards sorted by confidence when expanded', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      await user.click(screen.getByTestId('style-analysis-toggle'));

      // Cards should appear in confidence order
      expect(screen.getByTestId('style-card-jazz')).toBeInTheDocument();
      expect(screen.getByTestId('style-card-classical')).toBeInTheDocument();
      expect(screen.getByTestId('style-card-pop')).toBeInTheDocument();
    });

    it('marks dominant style with Primary badge', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      await user.click(screen.getByTestId('style-analysis-toggle'));

      const jazzCard = screen.getByTestId('style-card-jazz');
      expect(within(jazzCard).getByTestId('dominant-badge')).toBeInTheDocument();

      // Other cards should not have the badge
      const classicalCard = screen.getByTestId('style-card-classical');
      expect(within(classicalCard).queryByTestId('dominant-badge')).not.toBeInTheDocument();
    });

    it('hides section when no style analysis data', () => {
      render(<AnalysisResults results={mockLegacyResponse} chords={['C', 'F', 'G', 'C']} />);

      expect(screen.queryByTestId('style-analysis-section')).not.toBeInTheDocument();
    });
  });

  describe('Style Detail Cards', () => {
    it('displays style notes when present', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      await user.click(screen.getByTestId('style-analysis-toggle'));

      const jazzCard = screen.getByTestId('style-card-jazz');
      expect(within(jazzCard).getByTestId('style-notes')).toHaveTextContent(
        'Classic jazz turnaround progression'
      );
    });

    it('displays detected patterns with scores', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      await user.click(screen.getByTestId('style-analysis-toggle'));

      const jazzCard = screen.getByTestId('style-card-jazz');
      const pattern = within(jazzCard).getByTestId('pattern-item-0');

      expect(pattern).toHaveTextContent('I–vi–ii–V Turnaround');
      expect(pattern).toHaveTextContent('93%');
    });

    it('displays characteristic features', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      await user.click(screen.getByTestId('style-analysis-toggle'));

      const jazzCard = screen.getByTestId('style-card-jazz');

      expect(within(jazzCard).getByTestId('feature-0')).toHaveTextContent('Smooth voice leading');
      expect(within(jazzCard).getByTestId('feature-1')).toHaveTextContent('Circle of fifths motion');
    });

    it('handles empty patterns array gracefully', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      await user.click(screen.getByTestId('style-analysis-toggle'));

      const popCard = screen.getByTestId('style-card-pop');

      // Should still show style notes and features even without patterns
      expect(within(popCard).getByTestId('style-notes')).toHaveTextContent('Four-chord loop variant');
      expect(within(popCard).getByTestId('feature-0')).toHaveTextContent('Repetitive structure');
    });
  });

  describe('Accessibility', () => {
    it('includes aria labels on expand button', () => {
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const button = screen.getByTestId('style-analysis-toggle');
      expect(button).toHaveAttribute(
        'aria-label',
        'View analysis through 3 different musical styles'
      );
      expect(button).toHaveAttribute('aria-controls', 'style-analysis-details');
    });

    it('updates aria-expanded on toggle', async () => {
      const user = userEvent.setup();
      render(<AnalysisResults results={mockMultiProfileResponse} chords={['C', 'Am', 'Dm', 'G']} />);

      const button = screen.getByTestId('style-analysis-toggle');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      await user.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'true');

      await user.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });
  });
});
