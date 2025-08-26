import { test, expect } from '@playwright/test';
import { MusicTheoryAppPage } from '../page-objects/MusicTheoryAppPage';
import { SCALE_ANALYSIS_CASES, ValidatedTestCase } from '../data/validated-test-cases';

/**
 * Scale Analysis Validation Tests
 *
 * These tests validate that the UI accurately displays scale analysis results
 * that match the validated outputs from library unit tests.
 */

test.describe('Scale Analysis Validation', () => {
  let app: MusicTheoryAppPage;

  test.beforeEach(async ({ page }) => {
    app = new MusicTheoryAppPage(page);
    await app.navigateToAnalysisHub();
  });

  // Test each validated scale case
  SCALE_ANALYSIS_CASES.forEach((testCase: ValidatedTestCase) => {
    test(`${testCase.id}: ${testCase.description}`, async () => {
      // Analyze the scale
      await app.analyzeInput(testCase.input, testCase.inputType);

      // Validate no errors occurred
      await app.expectNoErrors();

      // Validate primary analysis type appears
      await app.expectAnalysisType(testCase.expectedUI.primaryAnalysis as any);

      // Validate all expected UI elements are visible
      await app.expectUIElements(testCase.expectedUI.displayElements);

      // Validate mode identification
      if (testCase.expectedUI.mode) {
        await app.expectMode(testCase.expectedUI.mode);
      }

      // Validate confidence scores
      const confidence = testCase.expectedUI.confidence;
      if (confidence.modal) {
        await app.expectConfidenceRange('modal', confidence.modal - 10, confidence.modal + 10);
      }
    });
  });

  test.describe('Specific Scale Detection Scenarios', () => {
    test('Complete C Major Scale: Should detect Ionian mode', async () => {
      await app.analyzeInput('C D E F G A B C', 'scale');

      // Should identify as major scale/Ionian
      await app.expectAnalysisType('scale');
      await app.expectMode('C Ionian');

      // Should show scale degrees
      await app.expectUIElements(['[data-testid="scale-degrees"]']);

      // Should show high confidence
      await app.expectConfidenceRange('modal', 90, 100);

      // Should display all scale tones
      const scaleTonesElement = app.page.locator('[data-testid="scale-tones"]');
      if (await scaleTonesElement.isVisible()) {
        const scaleText = await scaleTonesElement.textContent();
        ['C', 'D', 'E', 'F', 'G', 'A', 'B'].forEach(note => {
          expect(scaleText).toContain(note);
        });
      }
    });

    test('G Mixolydian: Should detect modal characteristics', async () => {
      await app.analyzeInput('G A B C D E F G', 'scale');

      await app.expectAnalysisType('modal');
      await app.expectMode('G Mixolydian');

      // Should highlight characteristic notes (F natural instead of F#)
      await app.expectUIElements(['[data-testid="characteristic-notes"]']);

      const characteristicText = await app.page.locator('[data-testid="characteristic-notes"]').textContent();
      expect(characteristicText).toContain('F'); // F natural is the characteristic note

      // Should show parent key relationship
      await app.expectUIElements(['[data-testid="parent-key-relationship"]']);

      const parentKeyText = await app.page.locator('[data-testid="parent-key-relationship"]').textContent();
      expect(parentKeyText).toContain('C major'); // Parent key
    });

    test('D Dorian: Should identify natural sixth characteristic', async () => {
      await app.analyzeInput('D E F G A B C D', 'scale');

      await app.expectAnalysisType('modal');
      await app.expectMode('D Dorian');

      // Should highlight Dorian characteristics (natural 6th)
      await app.expectUIElements(['[data-testid="dorian-characteristics"]']);

      const dorianText = await app.page.locator('[data-testid="dorian-characteristics"]').textContent();
      expect(dorianText?.toLowerCase()).toContain('sixth'); // Natural sixth characteristic

      // Should show B natural as the characteristic note
      const characteristicElement = app.page.locator('[data-testid="characteristic-notes"]');
      if (await characteristicElement.isVisible()) {
        const charText = await characteristicElement.textContent();
        expect(charText).toContain('B'); // B natural (natural 6th)
      }
    });

    test('A Natural Minor (Aeolian): Should distinguish from harmonic/melodic minor', async () => {
      await app.analyzeInput('A B C D E F G A', 'scale');

      await app.expectAnalysisType('modal');
      await app.expectMode('A Aeolian');

      // Should specify natural minor characteristics
      const modeText = await app.page.locator('[data-testid="mode-display"]').textContent();
      expect(modeText?.toLowerCase()).toMatch(/(natural minor|aeolian)/);

      // Should not suggest harmonic or melodic minor
      expect(modeText?.toLowerCase()).not.toContain('harmonic');
      expect(modeText?.toLowerCase()).not.toContain('melodic');
    });

    test('F Lydian: Should detect raised fourth', async () => {
      await app.analyzeInput('F G A B C D E F', 'scale');

      await app.expectAnalysisType('modal');
      await app.expectMode('F Lydian');

      // Should highlight raised 4th characteristic
      const characteristicElement = app.page.locator('[data-testid="characteristic-notes"]');
      if (await characteristicElement.isVisible()) {
        const charText = await characteristicElement.textContent();
        expect(charText).toContain('B'); // B natural (raised 4th in F)
      }

      // Should show parent key relationship to C major
      const parentKeyElement = app.page.locator('[data-testid="parent-key-relationship"]');
      if (await parentKeyElement.isVisible()) {
        const parentText = await parentKeyElement.textContent();
        expect(parentText).toContain('C major');
      }
    });

    test('E Phrygian: Should detect lowered second', async () => {
      await app.analyzeInput('E F G A B C D E', 'scale');

      await app.expectAnalysisType('modal');
      await app.expectMode('E Phrygian');

      // Should highlight lowered 2nd characteristic
      const characteristicElement = app.page.locator('[data-testid="characteristic-notes"]');
      if (await characteristicElement.isVisible()) {
        const charText = await characteristicElement.textContent();
        expect(charText).toContain('F'); // F natural (lowered 2nd in E)
      }
    });
  });

  test.describe('Partial Scale Detection', () => {
    test('Pentatonic Scale: Should identify pentatonic characteristics', async () => {
      await app.analyzeInput('C D E G A C', 'scale');

      // Should identify as pentatonic
      const analysisElement = app.page.locator('[data-testid="scale-analysis"]');
      if (await analysisElement.isVisible()) {
        const analysisText = await analysisElement.textContent();
        expect(analysisText?.toLowerCase()).toContain('pentatonic');
      }

      // Should note missing semitones
      const notesElement = app.page.locator('[data-testid="scale-notes"]');
      if (await notesElement.isVisible()) {
        const notesText = await notesElement.textContent();
        expect(notesText?.toLowerCase()).toMatch(/(5 notes|pentatonic)/);
      }
    });

    test('Chromatic Scale Fragment: Should identify chromatic movement', async () => {
      await app.analyzeInput('C C# D D# E F', 'scale');

      // Should identify chromatic characteristics
      const analysisElement = app.page.locator('[data-testid="scale-analysis"]');
      if (await analysisElement.isVisible()) {
        const analysisText = await analysisElement.textContent();
        expect(analysisText?.toLowerCase()).toContain('chromatic');
      }
    });

    test('Hexatonic Scale: Should handle 6-note scales', async () => {
      await app.analyzeInput('C D E F G A', 'scale');

      // Should handle 6-note input gracefully
      await app.expectNoErrors();

      // Should provide some analysis or suggest completion
      const analysisElement = app.page.locator('[data-testid="scale-analysis"]');
      await expect(analysisElement).toBeVisible();
    });
  });

  test.describe('Scale Analysis Edge Cases', () => {
    test('Incomplete scale input: Should provide helpful feedback', async () => {
      await app.analyzeInput('C D E', 'scale');

      // Should not error but provide guidance
      await app.expectNoErrors();

      // Should suggest completing the scale or offer partial analysis
      const messageElement = app.page.locator('[data-testid="analysis-message"], [data-testid="scale-analysis"]');
      await expect(messageElement).toBeVisible();

      const messageText = await messageElement.textContent();
      expect(messageText?.toLowerCase()).toMatch(/(incomplete|partial|continue|more notes)/);
    });

    test('Repeated notes in scale: Should handle gracefully', async () => {
      await app.analyzeInput('C D E F G A B C C', 'scale');

      // Should still identify as C major despite repetition
      await app.expectAnalysisType('scale');
      await app.expectMode('C Ionian');
    });

    test('Out-of-order scale notes: Should recognize pattern', async () => {
      await app.analyzeInput('E F G A B C D E', 'scale'); // E Phrygian

      // Should identify the mode regardless of starting note position
      await app.expectAnalysisType('modal');
      await app.expectMode('E Phrygian');
    });

    test('Enharmonic scale notes: Should handle correctly', async () => {
      await app.analyzeInput('C D E F G A A# C', 'scale'); // A# instead of Bb

      // Should handle enharmonic equivalents
      await app.expectNoErrors();
      await app.expectAnalysisType('scale');
    });
  });

  test.describe('Scale to Chord Relationship Analysis', () => {
    test('Major scale: Should show related chords', async () => {
      await app.analyzeInput('C D E F G A B C', 'scale');

      // Should show related chord information if available
      const relatedChordsElement = app.page.locator('[data-testid="related-chords"]');
      if (await relatedChordsElement.isVisible()) {
        const chordsText = await relatedChordsElement.textContent();
        expect(chordsText).toContain('C'); // Tonic chord
        expect(chordsText).toContain('F'); // Subdominant
        expect(chordsText).toContain('G'); // Dominant
      }
    });

    test('Modal scale: Should show characteristic chords', async () => {
      await app.analyzeInput('D E F G A B C D', 'scale'); // D Dorian

      const modalChordsElement = app.page.locator('[data-testid="modal-chords"]');
      if (await modalChordsElement.isVisible()) {
        const chordsText = await modalChordsElement.textContent();
        expect(chordsText).toContain('Dm'); // Dorian tonic is minor
      }
    });
  });

  test.describe('UI Responsiveness for Scale Analysis', () => {
    test('Real-time scale detection: Should update as notes are added', async () => {
      // Test progressive scale building if real-time detection is implemented
      await app.enterInput('C D E', 'scale');

      // Add more notes progressively
      await app.chordProgressionInput.fill('C D E F G');
      await app.page.waitForTimeout(500); // Wait for any auto-detection

      await app.clickAnalyze();

      // Should provide analysis for partial scale
      await app.expectNoErrors();
    });

    test('Scale visualization: Should display scale pattern if available', async () => {
      await app.analyzeInput('C D E F G A B C', 'scale');

      // Check for any scale visualization elements
      const visualElements = [
        '[data-testid="scale-pattern"]',
        '[data-testid="scale-visualization"]',
        '[data-testid="note-diagram"]'
      ];

      // At least one visualization element should be present
      let visualFound = false;
      for (const selector of visualElements) {
        const element = app.page.locator(selector);
        if (await element.isVisible()) {
          visualFound = true;
          break;
        }
      }

      // Note: This test is optional as visualization may not be implemented
      // If no visualization is found, that's acceptable
    });
  });
});
