import { test, expect } from '@playwright/test';
import { MusicTheoryAppPage } from '../page-objects/MusicTheoryAppPage';

/**
 * Enhanced Analysis Features Validation Tests
 *
 * These tests validate the sophisticated analysis features we implemented:
 * - Modal characteristics detection
 * - Secondary dominants analysis
 * - Parent key relationships
 * - Contextual classification
 * - Confidence breakdown
 * - Cadence detection
 * - Chord function analysis
 */

test.describe('Enhanced Analysis Features Validation', () => {
  let app: MusicTheoryAppPage;

  test.beforeEach(async ({ page }) => {
    app = new MusicTheoryAppPage(page);
    await app.navigateToAnalysisHub();
  });

  test.describe('Modal Characteristics Detection', () => {
    test('C-Bb-F-C: Mixolydian modal characteristics', async () => {
      // Opening move: analyze a classic Mixolydian progression
      await app.analyzeInput('C Bb F C', 'chord-progression');

      // Main play: verify modal analysis appears prominently
      await app.expectAnalysisType('modal');

      // Big play: check for specific modal characteristics
      await app.expectModalCharacteristics([
        'bVII chord (modal characteristic)',
        'Lowered 7th scale degree'
      ]);

      // Victory lap: verify parent key relationship
      await app.expectParentKeyRelationship('matches');
      await app.expectContextualClassification('modal_borrowing');

      // Final whistle: check confidence breakdown shows modal dominance
      await app.expectConfidenceBreakdown({ modal: 0.97 });
    });

    test('G-F-C-G: Different tonic, same modal characteristics', async () => {
      await app.analyzeInput('G F C G', 'chord-progression');

      await app.expectAnalysisType('modal');
      await app.expectMode('G Mixolydian');

      // Should still detect the characteristic bVII chord
      await app.expectModalCharacteristics(['bVII']);
    });
  });

  test.describe('Secondary Dominants Analysis', () => {
    test('C-A7-Dm-G-C: Classic V7/ii secondary dominant', async () => {
      // Opening move: analyze progression with clear secondary dominant
      await app.analyzeInput('C A7 Dm G C', 'chord-progression');

      // Main play: should detect the A7 → Dm secondary dominant relationship
      await app.expectSecondaryDominants([
        { chord: 'A7', target: 'Dm', roman: 'V7/ii' }
      ]);

      // Big play: verify this appears in both primary and alternative analyses
      await app.expectAnalysisType('modal'); // Primary might be modal

      // Victory lap: check alternative functional analysis includes it
      const altAnalysis = app.page.locator('.alternative-analysis').first();
      await expect(altAnalysis).toBeVisible();
      await expect(altAnalysis).toContainText('V7/ii');
    });

    test('C-E7-Am-D7-G-C: Multiple secondary dominants', async () => {
      await app.analyzeInput('C E7 Am D7 G C', 'chord-progression');

      // Should detect both E7 → Am (V7/vi) and D7 → G (V7/V)
      await app.expectSecondaryDominants([
        { chord: 'E7', target: 'Am', roman: 'V7/vi' },
        { chord: 'D7', target: 'G', roman: 'V7/V' }
      ]);
    });
  });

  test.describe('Functional Analysis Enhancements', () => {
    test('C-F-G-C: Clear functional progression with cadence', async () => {
      // Opening move: classic I-IV-V-I progression
      await app.analyzeInput('C F G C', 'chord-progression');

      await app.expectAnalysisType('functional');

      // Main play: verify chord functions flow
      await app.expectChordFunctions(['tonic', 'predominant', 'dominant', 'tonic']);

      // Big play: check for cadence detection
      await app.expectCadences([{ type: 'authentic' }]);

      // Victory lap: verify contextual classification
      await app.expectContextualClassification('diatonic');

      // Final whistle: confirm confidence breakdown
      await app.expectConfidenceBreakdown({ functional: 0.90 });
    });

    test('Am-Dm-G-C: ii-V-I with Roman numeral accuracy', async () => {
      await app.analyzeInput('Am Dm G C', 'chord-progression');

      await app.expectAnalysisType('functional');
      await app.expectRomanNumerals(['vi', 'ii', 'V', 'I']);
      await app.expectChordFunctions(['tonic', 'predominant', 'dominant', 'tonic']);
    });
  });

  test.describe('Contextual Classification', () => {
    test('C-F-G-C in C major: Diatonic classification', async () => {
      // This looks odd, but it tests our classification logic
      await app.analyzeInput('C F G C', 'chord-progression');
      await app.expectContextualClassification('diatonic');
    });

    test('D-C-G-D in C major: Modal borrowing classification', async () => {
      // Time to tackle the tricky bit - notes outside the given key
      await app.analyzeInput('D C G D', 'chord-progression');

      // This progression uses notes outside C major, so should be modal_borrowing
      await app.expectContextualClassification('modal_borrowing');
    });

    test('F#-B-E-F# with no parent key: Modal candidate', async () => {
      // Reset to no parent key context first
      const parentKeyInput = app.page.locator('#parentKey');
      await parentKeyInput.clear();

      await app.analyzeInput('F# B E F#', 'chord-progression');
      await app.expectContextualClassification('modal_candidate');
    });
  });

  test.describe('Alternative Analysis Validation', () => {
    test('Modal progression shows functional alternative', async () => {
      await app.analyzeInput('C Bb F C', 'chord-progression');

      // Primary should be modal
      await app.expectAnalysisType('modal');

      // Should show functional alternative with Roman numerals
      const alternatives = app.page.locator('.alternative-analysis');
      await expect(alternatives).toHaveCount(1);

      const functionalAlt = alternatives.first();
      await expect(functionalAlt).toContainText('functional');
      await expect(functionalAlt).toContainText('Roman Numerals');
    });

    test('Chromatic progression shows multiple interpretations', async () => {
      await app.analyzeInput('C A7 Dm G C', 'chord-progression');

      // Should have at least one alternative interpretation
      const alternatives = app.page.locator('.alternative-analysis');
      await expect(alternatives.first()).toBeVisible();

      // Alternative should include the chromatic analysis
      await expect(alternatives.first()).toContainText('V7/ii');
    });
  });

  test.describe('Confidence Breakdown Display', () => {
    test('Mixed progression shows multiple confidence scores', async () => {
      await app.analyzeInput('C A7 Dm G C', 'chord-progression');

      // Should show confidence breakdown with multiple analysis types
      await expect(app.confidenceBreakdown).toBeVisible();

      const breakdownText = await app.confidenceBreakdown.textContent();

      // Here's where we verify the confidence scoring is working
      expect(breakdownText).toMatch(/Modal:\s*0\.\d+/);

      // Alternative might show functional confidence
      const alternatives = app.page.locator('.alternative-analysis .confidence-breakdown');
      if (await alternatives.first().isVisible()) {
        const altText = await alternatives.first().textContent();
        expect(altText).toMatch(/Functional:\s*0\.\d+/);
      }
    });
  });

  test.describe('UI Integration and Display Quality', () => {
    test('Enhanced fields have proper visual styling', async () => {
      // Main play: analyze progression that triggers multiple enhanced features
      await app.analyzeInput('C A7 Dm G C', 'chord-progression');

      // Big play: verify all enhanced elements are styled properly
      await expect(app.secondaryDominants).toHaveCSS('background-color', /rgb\(255, 234, 167\)/); // Yellow background
      await expect(app.contextualClassification).toHaveCSS('background-color', /rgb\(232, 245, 232\)/); // Green background

      // Victory lap: check elements are properly spaced and readable
      const secondaryDominantsBox = await app.secondaryDominants.boundingBox();
      expect(secondaryDominantsBox?.height).toBeGreaterThan(30); // Should have decent height
    });

    test('Enhanced fields responsive behavior', async () => {
      await app.analyzeInput('C Bb F C', 'chord-progression');

      // Test different viewport sizes
      await app.page.setViewportSize({ width: 400, height: 800 }); // Mobile
      await expect(app.modalCharacteristics).toBeVisible();

      await app.page.setViewportSize({ width: 1200, height: 800 }); // Desktop
      await expect(app.modalCharacteristics).toBeVisible();
    });

    test('All enhanced fields appear in JSON modal', async () => {
      await app.analyzeInput('C A7 Dm G C', 'chord-progression');

      // Open the JSON response modal
      const viewResponseButton = app.page.locator('.view-response-button');
      await viewResponseButton.click();

      const jsonModal = app.page.locator('.modal-content');
      await expect(jsonModal).toBeVisible();

      const jsonText = await app.page.locator('.json-display').textContent();

      // This saves us from manual JSON parsing - check key fields exist
      expect(jsonText).toContain('modal_characteristics');
      expect(jsonText).toContain('secondary_dominants');
      expect(jsonText).toContain('contextual_classification');
      expect(jsonText).toContain('parent_key_relationship');

      // Close modal
      await app.page.keyboard.press('Escape');
      await expect(jsonModal).not.toBeVisible();
    });
  });

  test.describe('Error Handling for Enhanced Features', () => {
    test('Invalid progression gracefully handles enhanced analysis', async () => {
      // Opening move: try to trigger enhanced analysis with invalid input
      await app.enterInput('X Y Z', 'chord-progression');
      await app.clickAnalyze();

      // Main play: should show error without crashing enhanced features
      await expect(app.errorMessage).toBeVisible();

      // Victory lap: enhanced fields should not appear with invalid input
      await expect(app.modalCharacteristics).not.toBeVisible();
      await expect(app.secondaryDominants).not.toBeVisible();
    });

    test('Empty enhanced fields handled gracefully', async () => {
      // Simple progression that might not trigger all features
      await app.analyzeInput('C', 'chord-progression');

      // Should complete analysis without errors
      await app.expectNoErrors();

      // Empty enhanced fields should not break the UI
      // (They might not be visible, which is correct behavior)
    });
  });
});
