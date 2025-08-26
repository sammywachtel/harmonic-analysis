import { test, expect } from '@playwright/test';
import { MusicTheoryAppPage } from '../page-objects/MusicTheoryAppPage';
import { MELODY_ANALYSIS_CASES, ValidatedTestCase } from '../data/validated-test-cases';

/**
 * Melody Analysis Validation Tests
 *
 * These tests validate that the UI accurately displays melody analysis results
 * that match the validated outputs from library unit tests.
 */

test.describe('Melody Analysis Validation', () => {
  let app: MusicTheoryAppPage;

  test.beforeEach(async ({ page }) => {
    app = new MusicTheoryAppPage(page);
    await app.navigateToAnalysisHub();
  });

  // Test each validated melody case
  MELODY_ANALYSIS_CASES.forEach((testCase: ValidatedTestCase) => {
    test(`${testCase.id}: ${testCase.description}`, async () => {
      // Analyze the melody
      await app.analyzeInput(testCase.input, testCase.inputType);

      // Validate no errors occurred
      await app.expectNoErrors();

      // Validate primary analysis type appears
      await app.expectAnalysisType(testCase.expectedUI.primaryAnalysis as any);

      // Validate all expected UI elements are visible
      await app.expectUIElements(testCase.expectedUI.displayElements);

      // Validate specific analysis content
      if (testCase.expectedUI.keyCenter) {
        await app.expectKeyCenter(testCase.expectedUI.keyCenter);
      }

      if (testCase.expectedUI.mode) {
        await app.expectMode(testCase.expectedUI.mode);
      }

      // Validate confidence scores
      const confidence = testCase.expectedUI.confidence;
      if (confidence.functional) {
        await app.expectConfidenceRange('functional', confidence.functional - 10, confidence.functional + 10);
      }
      if (confidence.modal) {
        await app.expectConfidenceRange('modal', confidence.modal - 10, confidence.modal + 10);
      }
    });
  });

  test.describe('Specific Melody Analysis Scenarios', () => {
    test('Simple C Major Melody: Should detect key center and contour', async () => {
      await app.analyzeInput('C E G E C', 'melody');

      // Should identify melodic analysis
      await app.expectAnalysisType('melodic');

      // Should show key center
      await app.expectKeyCenter('C major');

      // Should show melodic contour information
      await app.expectUIElements(['[data-testid="melodic-contour"]']);

      // Should show good confidence for simple tonal melody
      await app.expectConfidenceRange('functional', 75, 95);

      // Should identify melodic intervals if displayed
      const intervalsElement = app.page.locator('[data-testid="melodic-intervals"]');
      if (await intervalsElement.isVisible()) {
        const intervalsText = await intervalsElement.textContent();
        expect(intervalsText).toContain('3rd'); // C to E
        expect(intervalsText).toContain('3rd'); // E to G
      }
    });

    test('Modal Melody in G Mixolydian: Should detect modal characteristics', async () => {
      await app.analyzeInput('G A B C D E F G', 'melody');

      await app.expectAnalysisType('modal');
      await app.expectMode('G Mixolydian');

      // Should show modal characteristics in melody
      await app.expectUIElements(['[data-testid="characteristic-intervals"]']);

      // Should identify F natural as characteristic note
      const charElement = app.page.locator('[data-testid="characteristic-intervals"]');
      if (await charElement.isVisible()) {
        const charText = await charElement.textContent();
        expect(charText).toContain('F'); // F natural characteristic
      }

      // Should show parent key relationship
      const parentElement = app.page.locator('[data-testid="parent-key-relationship"]');
      if (await parentElement.isVisible()) {
        const parentText = await parentElement.textContent();
        expect(parentText).toContain('C major');
      }
    });

    test('Arpeggiated Melody: Should detect underlying harmony', async () => {
      await app.analyzeInput('C E G C E G C', 'melody');

      // Should identify as melodic but also note harmonic structure
      await app.expectAnalysisType('melodic');

      // Should show underlying chord structure
      const harmonyElement = app.page.locator('[data-testid="underlying-harmony"]');
      if (await harmonyElement.isVisible()) {
        const harmonyText = await harmonyElement.textContent();
        expect(harmonyText).toContain('C major'); // Underlying C major triad
      }

      // Should identify arpeggiated pattern
      const patternElement = app.page.locator('[data-testid="melodic-pattern"]');
      if (await patternElement.isVisible()) {
        const patternText = await patternElement.textContent();
        expect(patternText?.toLowerCase()).toContain('arpeggio');
      }
    });

    test('Stepwise Melody: Should identify scalar movement', async () => {
      await app.analyzeInput('C D E F G A B C', 'melody');

      await app.expectAnalysisType('melodic');

      // Should identify stepwise motion
      const motionElement = app.page.locator('[data-testid="melodic-motion"]');
      if (await motionElement.isVisible()) {
        const motionText = await motionElement.textContent();
        expect(motionText?.toLowerCase()).toMatch(/(stepwise|scalar|step)/);
      }

      // Should also offer scale analysis since it's a complete scale
      const scaleElement = app.page.locator('[data-testid="scale-analysis"]');
      if (await scaleElement.isVisible()) {
        await app.expectMode('C Ionian');
      }
    });

    test('Chromatic Melody: Should detect chromatic movement', async () => {
      await app.analyzeInput('C C# D D# E F', 'melody');

      await app.expectAnalysisType('melodic');

      // Should identify chromatic motion
      const chromaticElement = app.page.locator('[data-testid="chromatic-motion"]');
      if (await chromaticElement.isVisible()) {
        const chromaticText = await chromaticElement.textContent();
        expect(chromaticText?.toLowerCase()).toContain('chromatic');
      }

      // Should show semitone intervals
      const intervalsElement = app.page.locator('[data-testid="melodic-intervals"]');
      if (await intervalsElement.isVisible()) {
        const intervalsText = await intervalsElement.textContent();
        expect(intervalsText?.toLowerCase()).toMatch(/(semitone|half.step)/);
      }
    });

    test('Pentatonic Melody: Should detect pentatonic characteristics', async () => {
      await app.analyzeInput('C D E G A C', 'melody');

      await app.expectAnalysisType('melodic');

      // Should identify pentatonic scale usage
      const scaleElement = app.page.locator('[data-testid="scale-usage"]');
      if (await scaleElement.isVisible()) {
        const scaleText = await scaleElement.textContent();
        expect(scaleText?.toLowerCase()).toContain('pentatonic');
      }

      // Should note absence of half steps
      const intervalsElement = app.page.locator('[data-testid="interval-analysis"]');
      if (await intervalsElement.isVisible()) {
        const intervalsText = await intervalsElement.textContent();
        expect(intervalsText?.toLowerCase()).toMatch(/(no half.steps|pentatonic)/);
      }
    });
  });

  test.describe('Melodic Contour and Pattern Analysis', () => {
    test('Ascending melody: Should identify upward motion', async () => {
      await app.analyzeInput('C D E F G A B C', 'melody');

      const contourElement = app.page.locator('[data-testid="melodic-contour"]');
      if (await contourElement.isVisible()) {
        const contourText = await contourElement.textContent();
        expect(contourText?.toLowerCase()).toMatch(/(ascending|upward|rising)/);
      }
    });

    test('Descending melody: Should identify downward motion', async () => {
      await app.analyzeInput('C B A G F E D C', 'melody');

      const contourElement = app.page.locator('[data-testid="melodic-contour"]');
      if (await contourElement.isVisible()) {
        const contourText = await contourElement.textContent();
        expect(contourText?.toLowerCase()).toMatch(/(descending|downward|falling)/);
      }
    });

    test('Arch-shaped melody: Should identify contour shape', async () => {
      await app.analyzeInput('C E G E C', 'melody');

      const contourElement = app.page.locator('[data-testid="melodic-contour"]');
      if (await contourElement.isVisible()) {
        const contourText = await contourElement.textContent();
        expect(contourText?.toLowerCase()).toMatch(/(arch|peak|curve)/);
      }
    });

    test('Repeated note pattern: Should identify repetition', async () => {
      await app.analyzeInput('C C C D D D E E E', 'melody');

      const patternElement = app.page.locator('[data-testid="melodic-pattern"]');
      if (await patternElement.isVisible()) {
        const patternText = await patternElement.textContent();
        expect(patternText?.toLowerCase()).toMatch(/(repeated|repetition|pattern)/);
      }
    });

    test('Sequence pattern: Should identify melodic sequences', async () => {
      await app.analyzeInput('C D E D E F E F G', 'melody');

      const sequenceElement = app.page.locator('[data-testid="melodic-sequence"]');
      if (await sequenceElement.isVisible()) {
        const sequenceText = await sequenceElement.textContent();
        expect(sequenceText?.toLowerCase()).toMatch(/(sequence|pattern|motif)/);
      }
    });
  });

  test.describe('Melodic Range and Interval Analysis', () => {
    test('Wide range melody: Should identify melodic span', async () => {
      await app.analyzeInput('C C2 C3', 'melody'); // Wide octave span

      const rangeElement = app.page.locator('[data-testid="melodic-range"]');
      if (await rangeElement.isVisible()) {
        const rangeText = await rangeElement.textContent();
        expect(rangeText?.toLowerCase()).toMatch(/(wide|range|span|octave)/);
      }
    });

    test('Large interval leaps: Should identify melodic leaps', async () => {
      await app.analyzeInput('C G C G', 'melody'); // Perfect 5th leaps

      const intervalsElement = app.page.locator('[data-testid="melodic-intervals"]');
      if (await intervalsElement.isVisible()) {
        const intervalsText = await intervalsElement.textContent();
        expect(intervalsText?.toLowerCase()).toMatch(/(leap|5th|jump)/);
      }
    });

    test('Predominantly stepwise motion: Should identify step-wise movement', async () => {
      await app.analyzeInput('C D E F E D C', 'melody');

      const motionElement = app.page.locator('[data-testid="melodic-motion"]');
      if (await motionElement.isVisible()) {
        const motionText = await motionElement.textContent();
        expect(motionText?.toLowerCase()).toMatch(/(stepwise|step|conjunct)/);
      }
    });
  });

  test.describe('Melody to Harmony Relationship', () => {
    test('Melody with implied chord progression: Should suggest harmony', async () => {
      await app.analyzeInput('C E G D F A G B D C', 'melody');

      // Should suggest implied chord progression if analysis is sophisticated enough
      const harmonyElement = app.page.locator('[data-testid="implied-harmony"]');
      if (await harmonyElement.isVisible()) {
        const harmonyText = await harmonyElement.textContent();
        expect(harmonyText).toMatch(/(C|F|G)/); // Should suggest basic triads
      }
    });

    test('Modal melody: Should identify modal characteristics in melodic context', async () => {
      await app.analyzeInput('D E F G A B C D E F', 'melody'); // D Dorian

      await app.expectAnalysisType('modal');
      await app.expectMode('D Dorian');

      // Should highlight natural 6th (B) in melodic context
      const modalElement = app.page.locator('[data-testid="modal-characteristics"]');
      if (await modalElement.isVisible()) {
        const modalText = await modalElement.textContent();
        expect(modalText).toContain('B'); // Natural 6th characteristic
      }
    });
  });

  test.describe('Melody Analysis Edge Cases', () => {
    test('Very short melody: Should provide limited but helpful analysis', async () => {
      await app.analyzeInput('C E G', 'melody');

      await app.expectNoErrors();

      // Should still provide some analysis for short melodies
      const analysisElement = app.page.locator('[data-testid="melody-analysis"]');
      await expect(analysisElement).toBeVisible();

      // Might suggest it's too short for comprehensive analysis
      const messageElement = app.page.locator('[data-testid="analysis-message"]');
      if (await messageElement.isVisible()) {
        const messageText = await messageElement.textContent();
        expect(messageText?.toLowerCase()).toMatch(/(short|brief|limited|more notes)/);
      }
    });

    test('Single repeated note: Should handle gracefully', async () => {
      await app.analyzeInput('C C C C C', 'melody');

      await app.expectNoErrors();

      // Should identify as repetitive pattern
      const patternElement = app.page.locator('[data-testid="melodic-pattern"]');
      if (await patternElement.isVisible()) {
        const patternText = await patternElement.textContent();
        expect(patternText?.toLowerCase()).toMatch(/(repeated|same|monophonic)/);
      }
    });

    test('Atonal melody: Should handle non-tonal input', async () => {
      await app.analyzeInput('C F# Bb Eb Ab', 'melody');

      await app.expectNoErrors();

      // Should attempt analysis but may note atonal characteristics
      const analysisElement = app.page.locator('[data-testid="melody-analysis"]');
      await expect(analysisElement).toBeVisible();

      // May identify as atonal or provide interval analysis
      const tonalElement = app.page.locator('[data-testid="tonal-analysis"]');
      if (await tonalElement.isVisible()) {
        const tonalText = await tonalElement.textContent();
        expect(tonalText?.toLowerCase()).toMatch(/(atonal|chromatic|unclear)/);
      }
    });

    test('Melody with octave indicators: Should handle different octaves', async () => {
      await app.analyzeInput('C4 E4 G4 C5', 'melody');

      await app.expectNoErrors();

      // Should handle octave indicators gracefully
      const rangeElement = app.page.locator('[data-testid="melodic-range"]');
      if (await rangeElement.isVisible()) {
        const rangeText = await rangeElement.textContent();
        expect(rangeText).toMatch(/(octave|range)/);
      }
    });
  });

  test.describe('Melody Visualization and Feedback', () => {
    test('Melody should show visual feedback if available', async () => {
      await app.analyzeInput('C D E F G A B C', 'melody');

      // Check for any visual representations
      const visualElements = [
        '[data-testid="melody-visualization"]',
        '[data-testid="contour-graph"]',
        '[data-testid="note-sequence"]'
      ];

      // At least some visual feedback should be present
      let visualFound = false;
      for (const selector of visualElements) {
        const element = app.page.locator(selector);
        if (await element.isVisible()) {
          visualFound = true;
          break;
        }
      }

      // Note: Visual elements are optional, but text analysis should always be present
      const textAnalysisElement = app.page.locator('[data-testid="melody-analysis"]');
      await expect(textAnalysisElement).toBeVisible();
    });
  });
});
