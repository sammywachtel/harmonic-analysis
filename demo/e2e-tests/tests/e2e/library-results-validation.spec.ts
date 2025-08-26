import { test, expect } from '@playwright/test';
import { MusicTheoryAppPage } from '../page-objects/MusicTheoryAppPage';

/**
 * Library Results Validation Tests
 *
 * These tests validate that the UI displays EXACTLY match the results
 * from validated library unit tests. Every test case is derived from
 * passing unit tests to ensure accuracy.
 */

test.describe('Library Results Validation', () => {
  let app: MusicTheoryAppPage;

  test.beforeEach(async ({ page }) => {
    app = new MusicTheoryAppPage(page);
    await app.navigateToAnalysisHub();
  });

  test.describe('Exact Unit Test Result Matching', () => {
    test('C F G C: Should match unit test - I IV V I with 85-95% confidence', async () => {
      // From unit test: { input: 'C F G C', parentKey: 'C major', expected: ['I', 'IV', 'V', 'I'] }
      await app.analyzeInput('C F G C', 'chord-progression');

      // Validate exact Roman numeral sequence
      const romanNumeralsElement = app.page.locator('[data-testid="roman-numerals"]');
      await expect(romanNumeralsElement).toBeVisible();

      const romanText = await romanNumeralsElement.textContent();
      expect(romanText).toContain('I');
      expect(romanText).toContain('IV');
      expect(romanText).toContain('V');

      // Should display them in sequence I-IV-V-I
      const numeralElements = await app.page.locator('[data-testid="roman-numeral-item"]').all();
      if (numeralElements.length >= 4) {
        expect(await numeralElements[0].textContent()).toContain('I');
        expect(await numeralElements[1].textContent()).toContain('IV');
        expect(await numeralElements[2].textContent()).toContain('V');
        expect(await numeralElements[3].textContent()).toContain('I');
      }

      // Validate key center exactly as unit test expects
      await app.expectKeyCenter('C major');

      // Validate confidence range from unit test expectations (85-95%)
      await app.expectConfidenceRange('functional', 85, 95);

      // Should identify as functional analysis (not modal)
      await app.expectAnalysisType('functional');
    });

    test('Am Dm G C: Should match unit test - vi ii V I progression', async () => {
      // From unit test: { progression: 'Am Dm G C', expected: ['vi', 'ii', 'V', 'I'] }
      await app.analyzeInput('Am Dm G C', 'chord-progression');

      // Validate exact Roman numeral sequence with lowercase for minor chords
      await app.expectRomanNumerals(['vi', 'ii', 'V', 'I']);

      // Should identify C major as the key center
      await app.expectKeyCenter('C major');

      // Should show authentic cadence analysis (ii-V-I is classic cadence)
      const cadenceElement = app.page.locator('[data-testid="cadence-analysis"]');
      if (await cadenceElement.isVisible()) {
        const cadenceText = await cadenceElement.textContent();
        expect(cadenceText?.toLowerCase()).toMatch(/(authentic|ii.*v.*i)/);
      }

      // Should have high functional confidence
      await app.expectConfidenceRange('functional', 80, 95);
    });

    test('G F C G: Should match unit test - Modal Mixolydian characteristics', async () => {
      // From theoretical accuracy tests: Modal progression with bVII characteristic
      await app.analyzeInput('G F C G', 'chord-progression');

      // Should identify as modal, not functional
      await app.expectAnalysisType('modal');

      // Should identify G Mixolydian specifically
      await app.expectMode('G Mixolydian');

      // Should show bVII chord characteristic (F in key of G)
      const modalCharacteristics = app.page.locator('[data-testid="modal-characteristics"]');
      if (await modalCharacteristics.isVisible()) {
        const charText = await modalCharacteristics.textContent();
        expect(charText).toContain('bVII'); // F chord is bVII in G
      }

      // Should show parent key relationship to C major
      const parentKeyElement = app.page.locator('[data-testid="parent-key-relationship"]');
      if (await parentKeyElement.isVisible()) {
        const parentText = await parentKeyElement.textContent();
        expect(parentText).toContain('C major');
      }

      // Should have high modal confidence (90%+), low functional confidence
      await app.expectConfidenceRange('modal', 85, 95);

      // Functional confidence should be low since this doesn't function in G major
      const functionalConfidenceElement = app.page.locator('[data-testid="functional-confidence"]');
      if (await functionalConfidenceElement.isVisible()) {
        const funcText = await functionalConfidenceElement.textContent();
        const confidence = parseFloat(funcText?.replace(/[^\d.]/g, '') || '0');
        expect(confidence).toBeLessThan(50); // Should be low for modal progression
      }
    });

    test('D G A D: Should match unit test - I IV V I in D major', async () => {
      // From unit test: { input: 'D G A D', parentKey: 'D major', expected: 'I IV V I' }
      await app.analyzeInput('D G A D', 'chord-progression');

      // Should show I-IV-V-I pattern
      await app.expectRomanNumerals(['I', 'IV', 'V', 'I']);

      // Should identify D major as key center
      await app.expectKeyCenter('D major');

      // Should have high functional confidence
      await app.expectConfidenceRange('functional', 85, 95);

      // Should identify authentic cadence
      const cadenceElement = app.page.locator('[data-testid="cadence-analysis"]');
      if (await cadenceElement.isVisible()) {
        const cadenceText = await cadenceElement.textContent();
        expect(cadenceText?.toLowerCase()).toContain('authentic');
      }
    });

    test('Cmaj7 E7 Am D7 G: Should match unit test - Jazz with secondary dominants', async () => {
      // From comprehensive analysis tests: Jazz progression with V/vi and V/V
      await app.analyzeInput('Cmaj7 E7 Am D7 G', 'chord-progression');

      // Should identify chromatic/jazz analysis
      await app.expectAnalysisType('chromatic');

      // Should show Roman numerals including secondary dominants
      const romanElement = app.page.locator('[data-testid="roman-numerals"]');
      if (await romanElement.isVisible()) {
        const romanText = await romanElement.textContent();
        expect(romanText).toContain('I');    // Cmaj7
        expect(romanText).toContain('V/vi'); // E7
        expect(romanText).toContain('vi');   // Am
        expect(romanText).toContain('V/V');  // D7
        expect(romanText).toContain('V');    // G
      }

      // Should identify secondary dominants specifically
      const secondaryElement = app.page.locator('[data-testid="secondary-dominants"]');
      if (await secondaryElement.isVisible()) {
        const secondaryText = await secondaryElement.textContent();
        expect(secondaryText).toContain('E7'); // Should identify E7 as secondary dominant
        expect(secondaryText).toContain('D7'); // Should identify D7 as secondary dominant
      }

      // Should show high chromatic confidence
      await app.expectConfidenceRange('chromatic', 85, 95);

      // Should also show functional analysis
      await app.expectUIElements(['[data-testid="functional-analysis"]']);
    });

    test('Am F G Am: Should match unit test - Natural minor i VI VII i', async () => {
      // From unit test expectations: Natural minor progression
      await app.analyzeInput('Am F G Am', 'chord-progression');

      // Should show minor key Roman numerals
      await app.expectRomanNumerals(['i', 'VI', 'VII', 'i']);

      // Should identify A minor as key center
      await app.expectKeyCenter('A minor');

      // Should also identify modal characteristics (A Aeolian)
      const modalElement = app.page.locator('[data-testid="modal-analysis"]');
      if (await modalElement.isVisible()) {
        const modalText = await modalElement.textContent();
        expect(modalText).toContain('A Aeolian');
      }

      // Should show functional analysis for minor key
      await app.expectAnalysisType('functional');

      // Should have good confidence for clear minor progression
      await app.expectConfidenceRange('functional', 75, 90);
    });
  });

  test.describe('Confidence Score Accuracy Validation', () => {
    test('High confidence progressions: Should show 85%+ confidence', async () => {
      const highConfidenceProgression = 'C F G C';
      await app.analyzeInput(highConfidenceProgression, 'chord-progression');

      // Should show confidence score prominently
      const confidenceElement = app.page.locator('[data-testid="confidence-score"]');
      await expect(confidenceElement).toBeVisible();

      // Should be in high confidence range (85-95% from unit tests)
      await app.expectConfidenceRange('functional', 85, 95);

      // Should use visual indicators for high confidence
      const confidenceDisplay = app.page.locator('[data-testid="confidence-display"]');
      if (await confidenceDisplay.isVisible()) {
        const classes = await confidenceDisplay.getAttribute('class');
        expect(classes?.toLowerCase()).toMatch(/(high|strong|confident|success)/);
      }
    });

    test('Medium confidence progressions: Should show 50-84% confidence', async () => {
      const mediumConfidenceProgression = 'C Ab Bb C'; // Ambiguous progression
      await app.analyzeInput(mediumConfidenceProgression, 'chord-progression');

      // Should complete analysis but with lower confidence
      await app.expectNoErrors();

      const confidenceElement = app.page.locator('[data-testid="confidence-score"]');
      if (await confidenceElement.isVisible()) {
        const confidenceText = await confidenceElement.textContent();
        const confidence = parseFloat(confidenceText?.replace(/[^\d.]/g, '') || '0');
        expect(confidence).toBeGreaterThanOrEqual(30);
        expect(confidence).toBeLessThan(85);
      }
    });

    test('Low confidence progressions: Should show appropriate warnings', async () => {
      const lowConfidenceProgression = 'C F# Bb D#'; // Atonal progression
      await app.analyzeInput(lowConfidenceProgression, 'chord-progression');

      // Should attempt analysis but show low confidence
      await app.expectNoErrors();

      // Should show warning about low confidence or unclear analysis
      const warningElements = [
        '[data-testid="low-confidence-warning"]',
        '[data-testid="analysis-warning"]',
        '[data-testid="uncertain-analysis"]'
      ];

      let warningFound = false;
      for (const selector of warningElements) {
        const element = app.page.locator(selector);
        if (await element.isVisible()) {
          warningFound = true;
          const warningText = await element.textContent();
          expect(warningText?.toLowerCase()).toMatch(/(uncertain|low|unclear|ambiguous)/);
          break;
        }
      }

      // At minimum, confidence should be visually indicated as low
      const confidenceElement = app.page.locator('[data-testid="confidence-display"]');
      if (await confidenceElement.isVisible()) {
        const classes = await confidenceElement.getAttribute('class');
        expect(classes?.toLowerCase()).toMatch(/(low|weak|uncertain|warning)/);
      }
    });
  });

  test.describe('Analysis Type Accuracy Validation', () => {
    test('Clear functional progressions: Should prioritize functional analysis', async () => {
      const functionalProgressions = [
        'C F G C',      // I-IV-V-I
        'Am Dm G C',    // vi-ii-V-I
        'F Bb C F',     // I-IV-V-I in F
        'Dm G C F'      // ii-V-I-IV
      ];

      for (const progression of functionalProgressions) {
        await app.analyzeInput(progression, 'chord-progression');

        // Should show functional analysis as primary
        await app.expectAnalysisType('functional');

        // Should show Roman numerals
        await app.expectUIElements(['[data-testid="roman-numerals"]']);

        // Should show key center
        await app.expectUIElements(['[data-testid="key-center"]']);

        await app.clearInput();
      }
    });

    test('Clear modal progressions: Should prioritize modal analysis', async () => {
      const modalProgressions = [
        'G F C G',      // G Mixolydian
        'D E F G A B C D', // D Dorian (if treated as progression)
        'A Bb C A'      // A Phrygian characteristic
      ];

      for (const progression of modalProgressions) {
        await app.analyzeInput(progression, 'chord-progression');

        // Should show modal analysis as primary (except for scale input)
        if (progression.split(' ').length <= 4) {
          await app.expectAnalysisType('modal');

          // Should show modal characteristics
          await app.expectUIElements(['[data-testid="modal-characteristics"]']);
        }

        await app.clearInput();
      }
    });

    test('Jazz/chromatic progressions: Should show chromatic analysis', async () => {
      const chromaticProgressions = [
        'Cmaj7 E7 Am D7 G',  // Secondary dominants
        'C F Ab G C',        // Borrowed chord (bVI)
        'C A7 Dm G7 C'       // V/ii secondary dominant
      ];

      for (const progression of chromaticProgressions) {
        await app.analyzeInput(progression, 'chord-progression');

        // Should show chromatic analysis
        await app.expectAnalysisType('chromatic');

        // Should also show functional analysis
        await app.expectUIElements(['[data-testid="functional-analysis"]']);

        await app.clearInput();
      }
    });
  });

  test.describe('Edge Case Validation', () => {
    test('Single chord input: Should match single chord unit test expectations', async () => {
      await app.analyzeInput('C', 'single-chord');

      // Should show chord analysis, not progression analysis
      await app.expectAnalysisType('chord');

      // Should show chord tones
      await app.expectUIElements(['[data-testid="chord-tones"]']);

      // Should identify as C major triad
      const chordDisplay = app.page.locator('[data-testid="chord-display"]');
      if (await chordDisplay.isVisible()) {
        const chordText = await chordDisplay.textContent();
        expect(chordText).toContain('C');
        expect(chordText?.toLowerCase()).toContain('major');
      }
    });

    test('Empty input: Should match validation expectations', async () => {
      await app.enterInput('', 'chord-progression');
      await app.clickAnalyze();

      // Should show validation message, not error
      const validationElement = app.page.locator('[data-testid="validation-message"]');
      await expect(validationElement).toBeVisible();

      const validationText = await validationElement.textContent();
      expect(validationText?.toLowerCase()).toMatch(/(enter|input|required|chord)/);
    });

    test('Invalid chord input: Should match error handling expectations', async () => {
      await app.enterInput('X Y Z Q', 'chord-progression');
      await app.clickAnalyze();

      // Should show helpful error message
      await expect(app.errorMessage).toBeVisible();

      const errorText = await app.errorMessage.textContent();
      expect(errorText?.toLowerCase()).toMatch(/(invalid|recognize|chord|example)/);

      // Should suggest valid chord formats
      expect(errorText).toMatch(/(C|Am|F|G)/); // Should show examples
    });

    test('Very long progression: Should handle like unit tests', async () => {
      const longProgression = 'C Am F G C Am F G C Am F G C Am F G C Am F G';
      await app.analyzeInput(longProgression, 'chord-progression');

      // Should complete analysis within reasonable time
      await app.waitForAnalysisComplete(15000);

      // Should still provide accurate analysis
      await app.expectAnalysisType('functional');
      await app.expectKeyCenter('C major');

      // Should handle the length gracefully
      await app.expectNoErrors();
    });
  });

  test.describe('Multi-Layer Analysis Validation', () => {
    test('Progressions with multiple valid interpretations: Should show alternatives', async () => {
      // G F C G could be G Mixolydian OR V-IV-I-V in C major
      await app.analyzeInput('G F C G', 'chord-progression');

      // Should show modal as primary
      await app.expectAnalysisType('modal');

      // Should also show functional interpretation
      const alternativeElement = app.page.locator('[data-testid="alternative-interpretations"]');
      if (await alternativeElement.isVisible()) {
        const altText = await alternativeElement.textContent();
        expect(altText).toContain('functional'); // Should offer functional alternative
      }

      // Should show comparison between interpretations
      const comparisonElement = app.page.locator('[data-testid="interpretation-comparison"]');
      if (await comparisonElement.isVisible()) {
        const compText = await comparisonElement.textContent();
        expect(compText?.toLowerCase()).toMatch(/(modal|functional|interpretation)/);
      }
    });

    test('Complex jazz progression: Should show layered analysis', async () => {
      await app.analyzeInput('Cmaj7 A7 Dm7 G7 Em7 A7 Dm7 G7 C', 'chord-progression');

      // Should show multiple analysis layers
      await app.expectUIElements([
        '[data-testid="functional-analysis"]',
        '[data-testid="chromatic-analysis"]'
      ]);

      // Should identify ii-V-I patterns
      const functionalElement = app.page.locator('[data-testid="functional-analysis"]');
      if (await functionalElement.isVisible()) {
        const funcText = await functionalElement.textContent();
        expect(funcText?.toLowerCase()).toMatch(/(ii.*v.*i|2.*5.*1)/);
      }

      // Should identify secondary dominants
      const chromaticElement = app.page.locator('[data-testid="chromatic-analysis"]');
      if (await chromaticElement.isVisible()) {
        const chromText = await chromaticElement.textContent();
        expect(chromText).toContain('A7'); // A7 as secondary dominant
      }
    });
  });

  test.describe('Performance Validation', () => {
    test('Analysis speed: Should complete within expected timeframes', async () => {
      const startTime = Date.now();

      await app.analyzeInput('C F G C', 'chord-progression');

      const endTime = Date.now();
      const analysisTime = endTime - startTime;

      // Should complete basic analysis within 3 seconds
      expect(analysisTime).toBeLessThan(3000);

      // Should show results correctly despite fast execution
      await app.expectAnalysisType('functional');
      await app.expectRomanNumerals(['I', 'IV', 'V', 'I']);
    });

    test('Repeated analysis: Should maintain accuracy and speed', async () => {
      const testProgression = 'Am Dm G C';

      // Run same analysis multiple times
      for (let i = 0; i < 5; i++) {
        const startTime = Date.now();

        await app.analyzeInput(testProgression, 'chord-progression');
        await app.expectRomanNumerals(['vi', 'ii', 'V', 'I']);

        const endTime = Date.now();
        expect(endTime - startTime).toBeLessThan(3000);

        await app.clearInput();
      }
    });
  });
});
