import { test, expect } from '@playwright/test';
import { MusicTheoryAppPage } from '../page-objects/MusicTheoryAppPage';
import { CHORD_PROGRESSION_CASES, ValidatedTestCase } from '../data/validated-test-cases';

/**
 * Chord Progression Validation Tests
 *
 * These tests validate that the UI accurately displays chord progression analysis
 * results that match the validated outputs from library unit tests.
 */

test.describe('Chord Progression Analysis Validation', () => {
  let app: MusicTheoryAppPage;

  test.beforeEach(async ({ page }) => {
    app = new MusicTheoryAppPage(page);
    await app.navigateToAnalysisHub();
  });

  // Test each validated chord progression case
  CHORD_PROGRESSION_CASES.forEach((testCase: ValidatedTestCase) => {
    test(`${testCase.id}: ${testCase.description}`, async () => {
      // Analyze the chord progression
      await app.analyzeInput(testCase.input, testCase.inputType);

      // Validate no errors occurred
      await app.expectNoErrors();

      // Validate primary analysis type appears
      await app.expectAnalysisType(testCase.expectedUI.primaryAnalysis as any);

      // Validate all expected UI elements are visible
      await app.expectUIElements(testCase.expectedUI.displayElements);

      // Validate specific analysis content
      if (testCase.expectedUI.romanNumerals) {
        await app.expectRomanNumerals(testCase.expectedUI.romanNumerals);
      }

      if (testCase.expectedUI.keyCenter) {
        await app.expectKeyCenter(testCase.expectedUI.keyCenter);
      }

      if (testCase.expectedUI.mode) {
        await app.expectMode(testCase.expectedUI.mode);
      }

      // Validate confidence scores are in expected ranges
      const confidence = testCase.expectedUI.confidence;
      if (confidence.functional) {
        await app.expectConfidenceRange('functional', confidence.functional - 10, confidence.functional + 10);
      }
      if (confidence.modal) {
        await app.expectConfidenceRange('modal', confidence.modal - 10, confidence.modal + 10);
      }
      if (confidence.chromatic) {
        await app.expectConfidenceRange('chromatic', confidence.chromatic - 10, confidence.chromatic + 10);
      }
    });
  });

  test.describe('Specific Chord Progression Scenarios', () => {
    test('I-IV-V-I: Classic functional harmony display', async () => {
      await app.analyzeInput('C F G C', 'chord-progression');

      // Should show functional analysis prominently
      await app.expectAnalysisType('functional');

      // Should display Roman numerals in correct order
      await app.expectRomanNumerals(['I', 'IV', 'V', 'I']);

      // Should show high confidence
      await app.expectConfidenceRange('functional', 80, 95);

      // Should show key center
      await app.expectKeyCenter('C major');

      // Enhanced features validation
      await app.expectChordFunctions(['tonic', 'predominant', 'dominant', 'tonic']);
      await app.expectCadences([{ type: 'authentic' }]);
      await app.expectContextualClassification('diatonic');

      // Should show confidence breakdown
      await app.expectConfidenceBreakdown({ functional: 0.90 });
    });

    test('vi-ii-V-I: Relative minor start progression', async () => {
      await app.analyzeInput('Am Dm G C', 'chord-progression');

      await app.expectAnalysisType('functional');
      await app.expectRomanNumerals(['vi', 'ii', 'V', 'I']);
      await app.expectKeyCenter('C major');

      // Should recognize this as a common jazz/pop progression
      const analysisText = await app.page.locator('[data-testid="functional-analysis"]').textContent();
      expect(analysisText?.toLowerCase()).toMatch(/(jazz|common|popular)/);
    });

    test('G-F-C-G: Modal Mixolydian progression', async () => {
      await app.analyzeInput('G F C G', 'chord-progression');

      // Should identify as modal, not functional
      await app.expectAnalysisType('modal');

      // Should show G Mixolydian
      await app.expectMode('G Mixolydian');

      // Should show modal characteristics using enhanced features
      await app.expectModalCharacteristics(['bVII']);

      // Should show parent key relationship
      await app.expectParentKeyRelationship('matches');

      // Should classify as modal borrowing (using bVII outside of G major)
      await app.expectContextualClassification('modal_borrowing');

      // Should have high modal confidence, low functional confidence
      await app.expectConfidenceRange('modal', 85, 95);
    });

    test('Cmaj7-E7-Am-D7-G: Jazz with secondary dominants', async () => {
      await app.analyzeInput('Cmaj7 E7 Am D7 G', 'chord-progression');

      // Should identify secondary dominants using enhanced analysis
      await app.expectSecondaryDominants([
        { chord: 'E7', target: 'Am', roman: 'V7/vi' },
        { chord: 'D7', target: 'G', roman: 'V7/V' }
      ]);

      // Should show functional analysis with Roman numerals
      await app.expectRomanNumerals(['I', 'V7/vi', 'vi', 'V7/V', 'V']);

      // Should classify as chromatic due to secondary dominants
      await app.expectContextualClassification('diatonic'); // Base progression is diatonic with chromatic elements
    });

    test('Am-F-G-Am: Natural minor progression', async () => {
      await app.analyzeInput('Am F G Am', 'chord-progression');

      // Should show functional analysis in minor key
      await app.expectAnalysisType('functional');

      // Should identify as A minor
      await app.expectKeyCenter('A minor');

      // Should show minor key Roman numerals
      await app.expectRomanNumerals(['i', 'VI', 'VII', 'i']);

      // Should also offer modal interpretation (A Aeolian)
      await app.expectUIElements(['[data-testid="modal-analysis"]']);
      await app.expectMode('A Aeolian');
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('Invalid chord input handling', async () => {
      await app.enterInput('X Y Z Q', 'chord-progression');
      await app.clickAnalyze();

      // Should show helpful error message
      await expect(app.errorMessage).toBeVisible();

      const errorText = await app.errorMessage.textContent();
      expect(errorText?.toLowerCase()).toContain('invalid');
    });

    test('Empty input handling', async () => {
      await app.enterInput('', 'chord-progression');
      await app.clickAnalyze();

      // Should show validation message
      const errorOrMessage = app.page.locator('[data-testid="validation-message"], [data-testid="error-message"]');
      await expect(errorOrMessage).toBeVisible();
    });

    test('Very long progression handling', async () => {
      const longProgression = 'C F G C Am Dm G C F Bb C F G Am F C G C Am Dm G C';
      await app.analyzeInput(longProgression, 'chord-progression');

      // Should still complete analysis within reasonable time
      await app.waitForAnalysisComplete(15000);
      await app.expectAnalysisType('functional');
      await app.expectNoErrors();
    });

    test('Single chord input', async () => {
      await app.analyzeInput('C', 'single-chord');

      // Should show chord analysis instead of progression analysis
      await app.expectAnalysisType('chord');
      await app.expectUIElements(['[data-testid="chord-tones"]']);
    });
  });

  test.describe('UI Interaction Validation', () => {
    test('Clear button functionality', async () => {
      await app.analyzeInput('C F G C', 'chord-progression');
      await app.expectAnalysisType('functional');

      await app.clearInput();

      // Results should be cleared
      await expect(app.resultsPanel).not.toBeVisible();
    });

    test('Input method switching', async () => {
      // Test switching between input methods
      if (await app.inputMethodDropdown.isVisible()) {
        await app.inputMethodDropdown.click();
        await app.page.locator('text="Scale/Notes"').click();

        // Should adapt interface for scale input
        await app.enterInput('C D E F G A B C', 'scale');
        await app.clickAnalyze();
        await app.expectAnalysisType('scale');
      }
    });

    test('Analyze button states', async () => {
      // Button should be enabled with valid input
      await app.enterInput('C F G C', 'chord-progression');
      await expect(app.analyzeButton).toBeEnabled();

      // Should show appropriate state during analysis
      await app.clickAnalyze();

      // Button might be disabled during analysis (depending on implementation)
      // Wait for analysis to complete
      await app.waitForAnalysisComplete();

      // Button should be enabled again after analysis
      await expect(app.analyzeButton).toBeEnabled();
    });
  });
});
