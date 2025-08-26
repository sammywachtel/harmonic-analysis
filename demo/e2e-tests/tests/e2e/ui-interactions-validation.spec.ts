import { test, expect } from '@playwright/test';
import { MusicTheoryAppPage } from '../page-objects/MusicTheoryAppPage';

/**
 * UI Interactions Validation Tests
 *
 * These tests validate that all UI components, buttons, inputs, modals,
 * and navigation work correctly and provide appropriate feedback.
 */

test.describe('UI Interactions Validation', () => {
  let app: MusicTheoryAppPage;

  test.beforeEach(async ({ page }) => {
    app = new MusicTheoryAppPage(page);
    await app.navigateToAnalysisHub();
  });

  test.describe('Button Interactions', () => {
    test('Analyze button: Should work correctly in all states', async () => {
      // Test enabled state with valid input
      await app.enterInput('C F G C', 'chord-progression');
      await expect(app.analyzeButton).toBeEnabled();
      await expect(app.analyzeButton).toBeVisible();

      // Test clicking analyze button
      await app.testButtonInteraction('[data-testid="analyze-button"]', 'analyze');

      // Should show results after analysis
      await expect(app.resultsPanel).toBeVisible();
    });

    test('Clear button: Should clear input and results', async () => {
      // Enter input and analyze
      await app.analyzeInput('C F G C', 'chord-progression');
      await expect(app.resultsPanel).toBeVisible();

      // Test clear button
      await app.testButtonInteraction('[data-testid="clear-button"]', 'clear');

      // Should clear both input and results
      await expect(app.chordProgressionInput).toHaveValue('');
      await expect(app.resultsPanel).not.toBeVisible();
    });

    test('Input method dropdown: Should switch methods correctly', async () => {
      if (await app.inputMethodDropdown.isVisible()) {
        // Test dropdown opens
        await app.inputMethodDropdown.click();

        // Should show method options
        const chordOption = app.page.locator('text="Chord Progression"');
        const scaleOption = app.page.locator('text="Scale/Notes"');
        const melodyOption = app.page.locator('text="Melody"');

        await expect(chordOption).toBeVisible();

        // Test switching to scale mode
        if (await scaleOption.isVisible()) {
          await scaleOption.click();

          // Interface should adapt for scale input
          await app.enterInput('C D E F G A B C', 'scale');
          await app.clickAnalyze();
          await app.expectAnalysisType('scale');
        }
      }
    });

    test('Modal buttons: Should open and close modals correctly', async () => {
      // Look for modal trigger buttons
      const modalTriggers = [
        '[data-testid="chord-builder-button"]',
        '[data-testid="help-button"]',
        '[data-testid="settings-button"]',
        '[data-testid="info-button"]'
      ];

      for (const triggerSelector of modalTriggers) {
        const trigger = app.page.locator(triggerSelector);
        if (await trigger.isVisible()) {
          await app.testModalInteraction(triggerSelector);
        }
      }
    });

    test('Navigation buttons: Should switch tabs correctly', async () => {
      await app.testNavigationInteraction();
    });
  });

  test.describe('Input Field Interactions', () => {
    test('Chord progression input: Should handle typing, selection, and clearing', async () => {
      await app.testInputInteraction();
    });

    test('Input validation: Should show appropriate feedback', async () => {
      // Test empty input
      await app.enterInput('', 'chord-progression');
      await app.clickAnalyze();

      // Should show validation message
      const validationElement = app.page.locator('[data-testid="validation-message"], [data-testid="error-message"]');
      await expect(validationElement).toBeVisible();

      // Test invalid chord input
      await app.enterInput('X Y Z Q', 'chord-progression');
      await app.clickAnalyze();

      // Should show helpful error message
      await expect(app.errorMessage).toBeVisible();
      const errorText = await app.errorMessage.textContent();
      expect(errorText?.toLowerCase()).toContain('invalid');
    });

    test('Input autocomplete/suggestions: Should provide helpful suggestions', async () => {
      // Start typing a partial chord
      await app.chordProgressionInput.click();
      await app.chordProgressionInput.type('C F');

      // Look for any suggestion dropdowns or autocomplete
      const suggestionElements = [
        '[data-testid="chord-suggestions"]',
        '[data-testid="autocomplete"]',
        '[data-testid="suggestions-dropdown"]'
      ];

      // Check if suggestions appear (optional feature)
      for (const selector of suggestionElements) {
        const element = app.page.locator(selector);
        if (await element.isVisible()) {
          // If suggestions exist, they should be helpful
          const suggestionText = await element.textContent();
          expect(suggestionText).toBeTruthy();
        }
      }
    });

    test('Input placeholder text: Should provide helpful guidance', async () => {
      const placeholder = await app.chordProgressionInput.getAttribute('placeholder');
      expect(placeholder).toBeTruthy();
      expect(placeholder?.toLowerCase()).toMatch(/(chord|progression|example)/);
    });

    test('Keyboard shortcuts: Should work for common actions', async () => {
      await app.chordProgressionInput.focus();

      // Test common keyboard shortcuts if implemented
      await app.chordProgressionInput.fill('C F G C');

      // Test Enter key to analyze (if implemented)
      await app.page.keyboard.press('Enter');

      // May trigger analysis or may not - both are acceptable
      // Just ensure it doesn't break the interface
      await app.expectNoErrors();
    });
  });

  test.describe('Modal Interactions', () => {
    test('Chord builder modal: Should build chords correctly', async () => {
      const chordBuilderButton = app.page.locator('[data-testid="chord-builder-button"]');

      if (await chordBuilderButton.isVisible()) {
        await chordBuilderButton.click();

        const modal = app.page.locator('[role="dialog"]');
        await expect(modal).toBeVisible();

        // Test chord building interface
        const chordButtons = modal.locator('button');
        const buttonCount = await chordButtons.count();

        if (buttonCount > 0) {
          // Click a few chord building buttons
          await chordButtons.nth(0).click(); // Might be root note

          // Should update chord display
          const chordDisplay = modal.locator('[data-testid="chord-display"]');
          if (await chordDisplay.isVisible()) {
            const chordText = await chordDisplay.textContent();
            expect(chordText).toBeTruthy();
          }
        }

        // Close modal
        await app.page.keyboard.press('Escape');
        await expect(modal).not.toBeVisible();
      }
    });

    test('Help modal: Should display helpful information', async () => {
      const helpButton = app.page.locator('[data-testid="help-button"]');

      if (await helpButton.isVisible()) {
        await helpButton.click();

        const helpModal = app.page.locator('[role="dialog"]');
        await expect(helpModal).toBeVisible();

        // Should contain helpful text
        const helpText = await helpModal.textContent();
        expect(helpText?.toLowerCase()).toMatch(/(help|instruction|guide|example)/);

        // Should have close button
        const closeButton = helpModal.locator('[data-testid="close-button"]');
        if (await closeButton.isVisible()) {
          await closeButton.click();
          await expect(helpModal).not.toBeVisible();
        }
      }
    });

    test('Settings modal: Should allow configuration changes', async () => {
      const settingsButton = app.page.locator('[data-testid="settings-button"]');

      if (await settingsButton.isVisible()) {
        await settingsButton.click();

        const settingsModal = app.page.locator('[role="dialog"]');
        await expect(settingsModal).toBeVisible();

        // Look for configuration options
        const configOptions = [
          '[data-testid="theme-setting"]',
          '[data-testid="notation-setting"]',
          '[data-testid="confidence-setting"]'
        ];

        for (const optionSelector of configOptions) {
          const option = settingsModal.locator(optionSelector);
          if (await option.isVisible()) {
            // Test toggling the option if it's a switch/checkbox
            if (await option.locator('input[type="checkbox"]').isVisible()) {
              await option.locator('input[type="checkbox"]').click();
            }
          }
        }

        await app.page.keyboard.press('Escape');
        await expect(settingsModal).not.toBeVisible();
      }
    });
  });

  test.describe('Navigation Interactions', () => {
    test('Tab navigation: Should switch between main sections', async () => {
      // Test Analysis Hub tab
      if (await app.analysisHubTab.isVisible()) {
        await app.analysisHubTab.click();

        const analysisContent = app.page.locator('[data-testid="analysis-hub-content"]');
        if (await analysisContent.isVisible()) {
          await expect(analysisContent).toBeVisible();
        }

        // Should have active state indicator
        const tabClasses = await app.analysisHubTab.getAttribute('class');
        expect(tabClasses).toMatch(/(active|selected|current)/);
      }

      // Test Scale Finder tab
      if (await app.scaleFinderTab.isVisible()) {
        await app.scaleFinderTab.click();

        const scaleContent = app.page.locator('[data-testid="scale-finder-content"]');
        if (await scaleContent.isVisible()) {
          await expect(scaleContent).toBeVisible();
        }
      }
    });

    test('Breadcrumb navigation: Should show current location', async () => {
      const breadcrumbs = app.page.locator('[data-testid="breadcrumbs"]');

      if (await breadcrumbs.isVisible()) {
        const breadcrumbText = await breadcrumbs.textContent();
        expect(breadcrumbText).toBeTruthy();
        expect(breadcrumbText?.toLowerCase()).toMatch(/(analysis|scale|home)/);
      }
    });

    test('Back/forward browser navigation: Should work correctly', async () => {
      // Navigate between tabs
      if (await app.scaleFinderTab.isVisible()) {
        await app.scaleFinderTab.click();
        await app.page.waitForTimeout(500);

        // Use browser back
        await app.page.goBack();
        await app.page.waitForTimeout(500);

        // Should return to previous state without errors
        await app.expectNoErrors();

        // Use browser forward
        await app.page.goForward();
        await app.page.waitForTimeout(500);

        await app.expectNoErrors();
      }
    });
  });

  test.describe('Responsive Design Interactions', () => {
    test('Mobile viewport: Should adapt interface correctly', async () => {
      // Set mobile viewport
      await app.page.setViewportSize({ width: 375, height: 667 });
      await app.page.reload();
      await app.waitForPageReady();

      // Interface should remain functional
      await app.enterInput('C F G C', 'chord-progression');
      await app.clickAnalyze();
      await app.expectAnalysisType('functional');

      // Navigation might be collapsed or adapted
      const mobileNav = app.page.locator('[data-testid="mobile-navigation"]');
      const hamburgerMenu = app.page.locator('[data-testid="hamburger-menu"]');

      // Either mobile nav exists or hamburger menu exists
      const hasMobileNav = await mobileNav.isVisible();
      const hasHamburger = await hamburgerMenu.isVisible();

      expect(hasMobileNav || hasHamburger).toBeTruthy();
    });

    test('Tablet viewport: Should provide optimal experience', async () => {
      // Set tablet viewport
      await app.page.setViewportSize({ width: 768, height: 1024 });
      await app.page.reload();
      await app.waitForPageReady();

      // Should maintain full functionality
      await app.analyzeInput('G F C G', 'chord-progression');
      await app.expectAnalysisType('modal');
      await app.expectNoErrors();
    });

    test('Large desktop viewport: Should use space effectively', async () => {
      // Set large desktop viewport
      await app.page.setViewportSize({ width: 1920, height: 1080 });
      await app.page.reload();
      await app.waitForPageReady();

      // Should show enhanced features or layout
      await app.analyzeInput('Cmaj7 E7 Am D7 G', 'chord-progression');
      await app.expectAnalysisType('chromatic');

      // Might show additional panels or information
      const enhancedElements = [
        '[data-testid="side-panel"]',
        '[data-testid="detailed-analysis"]',
        '[data-testid="expanded-view"]'
      ];

      // Check if any enhanced elements are visible (optional)
      for (const selector of enhancedElements) {
        const element = app.page.locator(selector);
        if (await element.isVisible()) {
          // Enhanced elements should add value
          const elementText = await element.textContent();
          expect(elementText).toBeTruthy();
        }
      }
    });
  });

  test.describe('Accessibility Interactions', () => {
    test('Keyboard navigation: Should be fully keyboard accessible', async () => {
      // Tab through all interactive elements
      await app.page.keyboard.press('Tab');

      // Should focus on input field
      const focusedElement = await app.page.evaluate(() => document.activeElement?.tagName);
      expect(['INPUT', 'BUTTON', 'SELECT']).toContain(focusedElement);

      // Continue tabbing through interface
      for (let i = 0; i < 10; i++) {
        await app.page.keyboard.press('Tab');
        await app.page.waitForTimeout(100);
      }

      // Should not get stuck or break
      await app.expectNoErrors();
    });

    test('Screen reader support: Should provide appropriate labels', async () => {
      // Check for aria-labels and proper semantic elements
      const inputLabel = await app.chordProgressionInput.getAttribute('aria-label');
      const analyzeLabel = await app.analyzeButton.getAttribute('aria-label');

      expect(inputLabel || await app.chordProgressionInput.getAttribute('placeholder')).toBeTruthy();
      expect(analyzeLabel || await app.analyzeButton.textContent()).toBeTruthy();

      // Check for proper heading structure
      const headings = app.page.locator('h1, h2, h3');
      const headingCount = await headings.count();
      expect(headingCount).toBeGreaterThan(0);
    });

    test('High contrast mode: Should remain usable', async () => {
      // Simulate high contrast mode by checking color contrast
      const buttonStyles = await app.analyzeButton.evaluate(el => {
        const styles = getComputedStyle(el);
        return {
          backgroundColor: styles.backgroundColor,
          color: styles.color,
          border: styles.border
        };
      });

      // Should have visible styling (non-transparent colors)
      expect(buttonStyles.backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
      expect(buttonStyles.color).not.toBe('rgba(0, 0, 0, 0)');
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('Network errors: Should handle gracefully', async () => {
      // Simulate network issues by intercepting requests
      await app.page.route('**/api/**', route => {
        route.abort('failed');
      });

      await app.enterInput('C F G C', 'chord-progression');
      await app.clickAnalyze();

      // Should show appropriate error message
      await expect(app.errorMessage).toBeVisible();
      const errorText = await app.errorMessage.textContent();
      expect(errorText?.toLowerCase()).toMatch(/(network|connection|error|try again)/);
    });

    test('Rapid clicking: Should handle multiple quick interactions', async () => {
      await app.enterInput('C F G C', 'chord-progression');

      // Click analyze button rapidly multiple times
      for (let i = 0; i < 5; i++) {
        await app.analyzeButton.click();
        await app.page.waitForTimeout(50);
      }

      // Should handle gracefully without breaking
      await app.expectNoErrors();

      // Should eventually complete analysis
      await app.waitForAnalysisComplete(15000);
      await app.expectAnalysisType('functional');
    });

    test('Page refresh during analysis: Should handle gracefully', async () => {
      await app.enterInput('C F G C', 'chord-progression');
      await app.clickAnalyze();

      // Refresh page immediately
      await app.page.reload();
      await app.waitForPageReady();

      // Should load clean state without errors
      await app.expectNoErrors();
      await expect(app.chordProgressionInput).toHaveValue('');
    });

    test('Very long session: Should maintain performance', async () => {
      // Perform many analyses to test for memory leaks
      const progressions = [
        'C F G C',
        'Am Dm G C',
        'G F C G',
        'Dm G Em Am',
        'F G Am F'
      ];

      for (let cycle = 0; cycle < 3; cycle++) {
        for (const progression of progressions) {
          await app.analyzeInput(progression, 'chord-progression');
          await app.clearInput();
        }
      }

      // Should still be responsive and error-free
      await app.expectNoErrors();
      await app.analyzeInput('C F G C', 'chord-progression');
      await app.expectAnalysisType('functional');
    });
  });
});
