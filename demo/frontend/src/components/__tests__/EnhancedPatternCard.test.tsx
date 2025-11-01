// Test suite for EnhancedPatternCard component
// Validates unified pattern display with educational content and fallback behavior

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EnhancedPatternCard } from '../EnhancedPatternCard';
import type { EducationalCard, FullExplanation } from '../../types/analysis';

describe('EnhancedPatternCard', () => {
  // Opening move: Setup test data
  const mockPattern = {
    start: 2,
    end: 4,
    pattern_id: 'functional.cadence.authentic.perfect',
    name: 'Perfect Authentic Cadence',
    family: 'cadence',
    score: 0.95,
    glossary: {
      definition: 'Perfect Authentic Cadence. V–I (or V7–I), both chords in root position...',
      example_in_C_major: 'G → C, with soprano on C (scale degree 1).',
      term: 'Perfect Authentic Cadence',
      type: 'cadence',
    },
    cadence_role: 'final',
    is_section_closure: false,
  };

  const mockEducationalContent: EducationalCard = {
    pattern_id: 'functional.cadence.authentic.perfect',
    title: 'Perfect Authentic Cadence (PAC)',
    summary: 'The strongest way to end a musical phrase - like a period at the end of a sentence.',
    category: 'cadential',
  };

  const mockExplanation: FullExplanation = {
    pattern_id: 'functional.cadence.authentic.perfect',
    title: 'Perfect Authentic Cadence (PAC)',
    hook: 'Picture this...',
    breakdown: ['Point 1', 'Point 2'],
    story: 'Long story...',
    composers: 'Beethoven, Mozart',
    examples: ['Example 1'],
    try_this: 'Try this exercise',
  };

  // Main play: Test rendering with educational content
  describe('With Educational Content', () => {
    it('renders educational title and summary', () => {
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
        />
      );

      expect(screen.getByText('Perfect Authentic Cadence (PAC)')).toBeInTheDocument();
      expect(screen.getByText(/The strongest way to end a musical phrase/)).toBeInTheDocument();
    });

    it('displays educational category badge', () => {
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
        />
      );

      expect(screen.getByText('cadential')).toBeInTheDocument();
    });

    it('shows pattern ID in monospace', () => {
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
        />
      );

      expect(screen.getByText('functional.cadence.authentic.perfect')).toBeInTheDocument();
    });

    it('shows "Learn more" button when explanation is provided', () => {
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
          explanation={mockExplanation}
        />
      );

      expect(screen.getByText('Learn more')).toBeInTheDocument();
    });

    it('does not show "Learn more" button without explanation', () => {
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
        />
      );

      expect(screen.queryByText('Learn more')).not.toBeInTheDocument();
    });
  });

  // Big play: Test rendering without educational content (fallback)
  describe('Without Educational Content (Fallback)', () => {
    it('renders pattern name when no educational title', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.getByText('Perfect Authentic Cadence')).toBeInTheDocument();
    });

    it('renders glossary definition when no educational summary', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.getByText(/Perfect Authentic Cadence\. V–I/)).toBeInTheDocument();
    });

    it('renders family as category when no educational category', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.getByText('cadence')).toBeInTheDocument();
    });

    it('does not show "Learn more" button', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.queryByText('Learn more')).not.toBeInTheDocument();
    });

    it('handles missing glossary gracefully', () => {
      const patternNoGlossary = { ...mockPattern, glossary: undefined };
      render(<EnhancedPatternCard pattern={patternNoGlossary} />);

      // Should still render pattern name
      expect(screen.getByText('Perfect Authentic Cadence')).toBeInTheDocument();
    });
  });

  // Victory lap: Test metadata display
  describe('Metadata Display', () => {
    it('displays score as percentage', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.getByText('Score: 95%')).toBeInTheDocument();
    });

    it('displays chord range', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.getByText(/Chords 2–4/)).toBeInTheDocument();
    });

    it('displays cadence role badge', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.getByText('final')).toBeInTheDocument();
    });

    it('displays section closure badge when applicable', () => {
      const patternWithClosure = { ...mockPattern, is_section_closure: true };
      render(<EnhancedPatternCard pattern={patternWithClosure} />);

      expect(screen.getByText('Section Closure')).toBeInTheDocument();
    });

    it('does not display section closure badge when false', () => {
      render(<EnhancedPatternCard pattern={mockPattern} />);

      expect(screen.queryByText('Section Closure')).not.toBeInTheDocument();
    });

    it('handles missing cadence role', () => {
      const patternNoRole = { ...mockPattern, cadence_role: undefined };
      render(<EnhancedPatternCard pattern={patternNoRole} />);

      // Should not crash, just not show the badge
      expect(screen.queryByText('final')).not.toBeInTheDocument();
    });
  });

  // Time to tackle the tricky bit: Test hover handlers
  describe('Hover Handlers', () => {
    it('calls onHover when mouse enters the card', async () => {
      const user = userEvent.setup();
      const onHover = vi.fn();
      const onLeave = vi.fn();

      const { container } = render(
        <EnhancedPatternCard
          pattern={mockPattern}
          onHover={onHover}
          onLeave={onLeave}
        />
      );

      const cardElement = container.querySelector('[role="region"]');
      expect(cardElement).toBeInTheDocument();

      if (cardElement) {
        await user.hover(cardElement);
        expect(onHover).toHaveBeenCalledWith('functional.cadence.authentic.perfect');
      }
    });

    it('calls onLeave when mouse exits the card', async () => {
      const user = userEvent.setup();
      const onHover = vi.fn();
      const onLeave = vi.fn();

      const { container } = render(
        <EnhancedPatternCard
          pattern={mockPattern}
          onHover={onHover}
          onLeave={onLeave}
        />
      );

      const cardElement = container.querySelector('[role="region"]');
      expect(cardElement).toBeInTheDocument();

      if (cardElement) {
        await user.hover(cardElement);
        await user.unhover(cardElement);
        expect(onLeave).toHaveBeenCalled();
      }
    });

    it('renders without errors when hover handlers are not provided', () => {
      expect(() => {
        render(<EnhancedPatternCard pattern={mockPattern} />);
      }).not.toThrow();
    });
  });

  // Here's where we test expand/collapse functionality
  describe('Learn More Expansion', () => {
    it('expands explanation when "Learn more" is clicked', async () => {
      const user = userEvent.setup();
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
          explanation={mockExplanation}
        />
      );

      const learnMoreButton = screen.getByText('Learn more');
      await user.click(learnMoreButton);

      // Should show explanation hook
      expect(screen.getByText(/Picture this\.\.\./)).toBeInTheDocument();
      // Button text should change
      expect(screen.getByText('Show less')).toBeInTheDocument();
    });

    it('collapses explanation when "Show less" is clicked', async () => {
      const user = userEvent.setup();
      render(
        <EnhancedPatternCard
          pattern={mockPattern}
          educationalContent={mockEducationalContent}
          explanation={mockExplanation}
        />
      );

      // Expand first
      const learnMoreButton = screen.getByText('Learn more');
      await user.click(learnMoreButton);

      // Then collapse
      const showLessButton = screen.getByText('Show less');
      await user.click(showLessButton);

      // Explanation should be hidden
      expect(screen.queryByText(/Picture this\.\.\./)).not.toBeInTheDocument();
      // Button text should change back
      expect(screen.getByText('Learn more')).toBeInTheDocument();
    });
  });

  // Final whistle: Test edge cases
  describe('Edge Cases', () => {
    it('handles pattern with no family', () => {
      const patternNoFamily = { ...mockPattern, family: '' };
      render(<EnhancedPatternCard pattern={patternNoFamily} />);

      // Should still render without crashing
      expect(screen.getByText('Perfect Authentic Cadence')).toBeInTheDocument();
    });

    it('handles zero score', () => {
      const patternZeroScore = { ...mockPattern, score: 0 };
      render(<EnhancedPatternCard pattern={patternZeroScore} />);

      expect(screen.getByText('Score: 0%')).toBeInTheDocument();
    });

    it('handles pattern spanning single chord', () => {
      const patternSingleChord = { ...mockPattern, start: 2, end: 2 };
      render(<EnhancedPatternCard pattern={patternSingleChord} />);

      expect(screen.getByText(/Chords 2–2/)).toBeInTheDocument();
    });

    it('rounds score to nearest integer', () => {
      const patternDecimalScore = { ...mockPattern, score: 0.8567 };
      render(<EnhancedPatternCard pattern={patternDecimalScore} />);

      expect(screen.getByText('Score: 86%')).toBeInTheDocument();
    });
  });
});
