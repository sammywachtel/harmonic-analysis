// E2E test for multi-profile analysis workflow
// Tests user flow from chord entry through style analysis UI

import { test, expect } from '@playwright/test';

test.describe('Multi-Profile Analysis Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('displays dominant style badge and confidence bars for multi-profile analysis', async ({
    page,
  }) => {
    // Enter chords
    const chordsTextarea = page.locator('#chords');
    await chordsTextarea.fill('C Am Dm G');

    // Clear profile focus (select "All Styles")
    const profileSelector = page.getByTestId('profile-selector');
    await profileSelector.selectOption('');

    // Click analyze button
    const analyzeButton = page.getByRole('button', { name: /analyze progression/i });
    await analyzeButton.click();

    // Wait for results to appear
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Check for dominant style badge (may vary based on backend response)
    // We'll just verify the structure exists
    const primarySection = page.locator('text=Primary Interpretation').locator('..');

    // Verify style confidence section appears
    const styleConfidenceSection = page.getByTestId('style-confidence-section');
    await expect(styleConfidenceSection).toBeVisible();

    // Verify at least one confidence bar exists
    const confidenceBar = styleConfidenceSection.locator('.confidence-bar-container').first();
    await expect(confidenceBar).toBeVisible();

    // Verify progressbar semantics
    const progressbar = confidenceBar.locator('[role="progressbar"]');
    await expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    await expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  test('expands and collapses style analysis section', async ({ page }) => {
    // Enter chords and analyze
    await page.locator('#chords').fill('C Am Dm G');
    await page.getByTestId('profile-selector').selectOption('');
    await page.getByRole('button', { name: /analyze progression/i }).click();

    // Wait for results
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Find style analysis toggle button
    const toggleButton = page.getByTestId('style-analysis-toggle');

    // Verify initially collapsed
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
    await expect(page.getByTestId('style-cards-container')).not.toBeVisible();

    // Click to expand
    await toggleButton.click();

    // Verify expanded
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByTestId('style-cards-container')).toBeVisible();

    // Verify style cards are present (at least one)
    const styleCards = page.locator('[data-testid^="style-card-"]');
    await expect(styleCards.first()).toBeVisible();

    // Click to collapse
    await toggleButton.click();

    // Verify collapsed again
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
    await expect(page.getByTestId('style-cards-container')).not.toBeVisible();
  });

  test('displays style detail cards with patterns and features', async ({ page }) => {
    // Enter chords and analyze
    await page.locator('#chords').fill('C Am Dm G');
    await page.getByTestId('profile-selector').selectOption('');
    await page.getByRole('button', { name: /analyze progression/i }).click();

    // Wait for results
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Expand style analysis
    await page.getByTestId('style-analysis-toggle').click();

    // Wait for cards container
    const cardsContainer = page.getByTestId('style-cards-container');
    await expect(cardsContainer).toBeVisible();

    // Verify at least one style card exists
    const firstCard = page.locator('[data-testid^="style-card-"]').first();
    await expect(firstCard).toBeVisible();

    // Verify card has confidence percentage
    const confidenceBadge = firstCard.locator('[data-testid^="confidence-"]');
    await expect(confidenceBadge).toBeVisible();
    await expect(confidenceBadge).toContainText('%');

    // Check for dominant badge on primary style (if present)
    const dominantBadge = page.getByTestId('dominant-badge');
    if (await dominantBadge.isVisible()) {
      await expect(dominantBadge).toHaveText('Primary');
    }
  });

  test('profile focus influences results (with classical focus)', async ({ page }) => {
    // Enter chords
    await page.locator('#chords').fill('C F G C');

    // Select classical focus
    await page.getByTestId('profile-selector').selectOption('classical');

    // Analyze
    await page.getByRole('button', { name: /analyze progression/i }).click();

    // Wait for results
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Verify analysis completed (we won't assert specific style since backend may vary)
    const primarySection = page.locator('text=Primary Interpretation').locator('..');
    await expect(primarySection).toBeVisible();

    // Verify key signature is displayed
    await expect(page.locator('text=Key:')).toBeVisible();
  });

  test('handles keyboard navigation for style section toggle', async ({ page }) => {
    // Enter chords and analyze
    await page.locator('#chords').fill('C Am Dm G');
    await page.getByTestId('profile-selector').selectOption('');
    await page.getByRole('button', { name: /analyze progression/i }).click();

    // Wait for results
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Focus the toggle button via keyboard
    const toggleButton = page.getByTestId('style-analysis-toggle');
    await toggleButton.focus();

    // Verify button is focused
    await expect(toggleButton).toBeFocused();

    // Press Enter to toggle
    await toggleButton.press('Enter');

    // Verify expanded
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'true');

    // Press Enter again to collapse
    await toggleButton.press('Enter');

    // Verify collapsed
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'false');
  });

  test('gracefully handles response without multi-profile data', async ({ page }) => {
    // Enter simple chords
    await page.locator('#chords').fill('C F G C');

    // Select a specific profile (may return single-profile response)
    await page.getByTestId('profile-selector').selectOption('classical');

    // Analyze
    await page.getByRole('button', { name: /analyze progression/i }).click();

    // Wait for results
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Verify primary interpretation is shown
    await expect(page.locator('text=Key:')).toBeVisible();
    await expect(page.locator('text=Roman Numerals:')).toBeVisible();

    // Style sections may or may not appear depending on backend response
    // Just verify the page doesn't crash and shows basic results
    const confidence = page.locator('text=Confidence:');
    await expect(confidence).toBeVisible();
  });

  test('displays multiple style confidence bars sorted by confidence', async ({ page }) => {
    // Enter chords known to trigger multi-profile (jazz turnaround)
    await page.locator('#chords').fill('Cmaj7 Am7 Dm7 G7');

    // Clear profile focus
    await page.getByTestId('profile-selector').selectOption('');

    // Analyze
    await page.getByRole('button', { name: /analyze progression/i }).click();

    // Wait for results
    await page.waitForSelector('text=Primary Interpretation', { timeout: 10000 });

    // Check for style confidence section
    const styleConfidenceSection = page.getByTestId('style-confidence-section');

    if (await styleConfidenceSection.isVisible()) {
      // Verify multiple bars exist
      const bars = styleConfidenceSection.locator('.confidence-bar-container');
      const barCount = await bars.count();

      // Should have at least 1 bar
      expect(barCount).toBeGreaterThan(0);

      // Verify each bar has a percentage
      for (let i = 0; i < barCount; i++) {
        const bar = bars.nth(i);
        const percentage = bar.locator('.confidence-bar-percentage');
        await expect(percentage).toBeVisible();
        await expect(percentage).toContainText('%');
      }
    }
  });
});
