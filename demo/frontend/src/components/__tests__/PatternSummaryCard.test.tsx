// Test suite for PatternSummaryCard component
// Validates hover handlers and educational content display

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PatternSummaryCard } from '../PatternSummaryCard';
import type { EducationalCard } from '../../types/analysis';

describe('PatternSummaryCard', () => {
  // Opening move: Setup test data
  const mockCard: EducationalCard = {
    pattern_id: 'cadence.authentic.perfect',
    title: 'Perfect Authentic Cadence (PAC)',
    summary: 'The strongest way to end a musical phrase',
    category: 'cadential',
    difficulty: 'beginner',
  };

  // Main play: Test basic rendering
  it('renders card with title and summary', () => {
    render(<PatternSummaryCard card={mockCard} />);

    expect(screen.getByText('Perfect Authentic Cadence (PAC)')).toBeInTheDocument();
    expect(screen.getByText('The strongest way to end a musical phrase')).toBeInTheDocument();
  });

  // Big play: Test hover handlers
  it('calls onHover when mouse enters the card', async () => {
    const user = userEvent.setup();
    const onHover = vi.fn();
    const onLeave = vi.fn();

    const { container } = render(
      <PatternSummaryCard card={mockCard} onHover={onHover} onLeave={onLeave} />
    );

    const cardElement = container.querySelector('[role="region"]');
    expect(cardElement).toBeInTheDocument();

    // Time to tackle the tricky bit: Simulate mouse enter
    if (cardElement) {
      await user.hover(cardElement);
      expect(onHover).toHaveBeenCalledWith('cadence.authentic.perfect');
    }
  });

  // Victory lap: Test leave handler
  it('calls onLeave when mouse exits the card', async () => {
    const user = userEvent.setup();
    const onHover = vi.fn();
    const onLeave = vi.fn();

    const { container } = render(
      <PatternSummaryCard card={mockCard} onHover={onHover} onLeave={onLeave} />
    );

    const cardElement = container.querySelector('[role="region"]');
    expect(cardElement).toBeInTheDocument();

    // Here's where we simulate mouse leave
    if (cardElement) {
      await user.hover(cardElement);
      await user.unhover(cardElement);
      expect(onLeave).toHaveBeenCalled();
    }
  });

  // Main play: Test optional handlers
  it('renders without errors when hover handlers are not provided', () => {
    expect(() => {
      render(<PatternSummaryCard card={mockCard} />);
    }).not.toThrow();
  });

  // Big play: Test category badge rendering
  it('displays category badge when category is provided', () => {
    render(<PatternSummaryCard card={mockCard} />);
    expect(screen.getByText('cadential')).toBeInTheDocument();
  });

  // Victory lap: Test expand/collapse functionality
  it('shows "Learn more" button when explanation is provided', () => {
    const mockExplanation = {
      pattern_id: 'cadence.authentic.perfect',
      title: 'Perfect Authentic Cadence (PAC)',
      hook: 'Picture this...',
      breakdown: ['Point 1', 'Point 2'],
      story: 'Long story...',
      composers: 'Beethoven, Mozart',
      examples: ['Example 1'],
      try_this: 'Try this exercise',
    };

    render(<PatternSummaryCard card={mockCard} explanation={mockExplanation} />);
    expect(screen.getByText('Learn more')).toBeInTheDocument();
  });
});
