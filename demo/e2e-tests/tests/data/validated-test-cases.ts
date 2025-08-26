/**
 * Validated Test Cases
 *
 * All test cases in this file are derived from passing unit tests in the main library.
 * These represent known-good results that the UI should accurately display.
 */

export interface ValidatedTestCase {
  id: string;
  description: string;
  input: string;
  inputType: 'chord-progression' | 'scale' | 'melody' | 'single-chord';
  parentKey?: string;
  expectedUI: {
    primaryAnalysis: string;
    romanNumerals?: string[];
    keyCenter?: string;
    mode?: string;
    confidence: {
      functional?: number;
      modal?: number;
      chromatic?: number;
    };
    displayElements: string[];
  };
}

// Chord Progression Test Cases (from unit tests)
export const CHORD_PROGRESSION_CASES: ValidatedTestCase[] = [
  {
    id: 'prog-1',
    description: 'Classic I-IV-V-I progression in C major',
    input: 'C F G C',
    inputType: 'chord-progression',
    parentKey: 'C major',
    expectedUI: {
      primaryAnalysis: 'functional',
      romanNumerals: ['I', 'IV', 'V', 'I'],
      keyCenter: 'C major',
      confidence: {
        functional: 90, // Expected 85-95% from unit tests
      },
      displayElements: [
        '[data-testid="functional-analysis"]',
        '[data-testid="roman-numerals"]',
        '[data-testid="confidence-score"]'
      ]
    }
  },
  {
    id: 'prog-2',
    description: 'vi-ii-V-I progression (relative minor start)',
    input: 'Am Dm G C',
    inputType: 'chord-progression',
    parentKey: 'C major',
    expectedUI: {
      primaryAnalysis: 'functional',
      romanNumerals: ['vi', 'ii', 'V', 'I'],
      keyCenter: 'C major',
      confidence: {
        functional: 85,
      },
      displayElements: [
        '[data-testid="functional-analysis"]',
        '[data-testid="roman-numerals"]',
        '[data-testid="cadence-analysis"]'
      ]
    }
  },
  {
    id: 'prog-3',
    description: 'Modal progression - G Mixolydian characteristic',
    input: 'G F C G',
    inputType: 'chord-progression',
    parentKey: 'C major',
    expectedUI: {
      primaryAnalysis: 'modal',
      mode: 'G Mixolydian',
      confidence: {
        modal: 90,
        functional: 30
      },
      displayElements: [
        '[data-testid="modal-analysis"]',
        '[data-testid="modal-characteristics"]',
        '[data-testid="parent-key-relationship"]'
      ]
    }
  },
  {
    id: 'prog-4',
    description: 'Jazz progression with secondary dominants',
    input: 'Cmaj7 E7 Am D7 G',
    inputType: 'chord-progression',
    parentKey: 'C major',
    expectedUI: {
      primaryAnalysis: 'chromatic',
      romanNumerals: ['I', 'V/vi', 'vi', 'V/V', 'V'],
      keyCenter: 'C major',
      confidence: {
        functional: 85,
        chromatic: 90
      },
      displayElements: [
        '[data-testid="functional-analysis"]',
        '[data-testid="chromatic-analysis"]',
        '[data-testid="secondary-dominants"]'
      ]
    }
  },
  {
    id: 'prog-5',
    description: 'Natural minor progression',
    input: 'Am F G Am',
    inputType: 'chord-progression',
    parentKey: 'A minor',
    expectedUI: {
      primaryAnalysis: 'functional',
      romanNumerals: ['i', 'VI', 'VII', 'i'],
      keyCenter: 'A minor',
      mode: 'A Aeolian',
      confidence: {
        functional: 80,
        modal: 90
      },
      displayElements: [
        '[data-testid="functional-analysis"]',
        '[data-testid="modal-analysis"]',
        '[data-testid="minor-key-analysis"]'
      ]
    }
  }
];

// Scale Analysis Test Cases
export const SCALE_ANALYSIS_CASES: ValidatedTestCase[] = [
  {
    id: 'scale-1',
    description: 'Complete C major scale detection',
    input: 'C D E F G A B C',
    inputType: 'scale',
    expectedUI: {
      primaryAnalysis: 'scale',
      mode: 'C Ionian (C Major)',
      confidence: {
        modal: 95
      },
      displayElements: [
        '[data-testid="scale-analysis"]',
        '[data-testid="mode-identification"]',
        '[data-testid="scale-degrees"]'
      ]
    }
  },
  {
    id: 'scale-2',
    description: 'G Mixolydian scale (F natural instead of F#)',
    input: 'G A B C D E F G',
    inputType: 'scale',
    expectedUI: {
      primaryAnalysis: 'modal',
      mode: 'G Mixolydian',
      confidence: {
        modal: 92
      },
      displayElements: [
        '[data-testid="modal-analysis"]',
        '[data-testid="characteristic-notes"]',
        '[data-testid="parent-key-relationship"]'
      ]
    }
  },
  {
    id: 'scale-3',
    description: 'D Dorian scale detection',
    input: 'D E F G A B C D',
    inputType: 'scale',
    expectedUI: {
      primaryAnalysis: 'modal',
      mode: 'D Dorian',
      confidence: {
        modal: 88
      },
      displayElements: [
        '[data-testid="modal-analysis"]',
        '[data-testid="dorian-characteristics"]',
        '[data-testid="natural-sixth"]'
      ]
    }
  }
];

// Melody Analysis Test Cases
export const MELODY_ANALYSIS_CASES: ValidatedTestCase[] = [
  {
    id: 'melody-1',
    description: 'Simple melodic line in C major',
    input: 'C E G E C',
    inputType: 'melody',
    expectedUI: {
      primaryAnalysis: 'melodic',
      keyCenter: 'C major',
      confidence: {
        functional: 85
      },
      displayElements: [
        '[data-testid="melody-analysis"]',
        '[data-testid="key-center"]',
        '[data-testid="melodic-contour"]'
      ]
    }
  },
  {
    id: 'melody-2',
    description: 'Modal melody with characteristic intervals',
    input: 'G A B C D E F G',
    inputType: 'melody',
    expectedUI: {
      primaryAnalysis: 'modal',
      mode: 'G Mixolydian',
      confidence: {
        modal: 90
      },
      displayElements: [
        '[data-testid="modal-analysis"]',
        '[data-testid="melodic-mode"]',
        '[data-testid="characteristic-intervals"]'
      ]
    }
  }
];

// Single Chord Test Cases
export const SINGLE_CHORD_CASES: ValidatedTestCase[] = [
  {
    id: 'chord-1',
    description: 'C major triad',
    input: 'C',
    inputType: 'single-chord',
    expectedUI: {
      primaryAnalysis: 'chord',
      displayElements: [
        '[data-testid="chord-analysis"]',
        '[data-testid="chord-tones"]',
        '[data-testid="chord-quality"]'
      ]
    }
  },
  {
    id: 'chord-2',
    description: 'A minor seventh chord',
    input: 'Am7',
    inputType: 'single-chord',
    expectedUI: {
      primaryAnalysis: 'chord',
      displayElements: [
        '[data-testid="chord-analysis"]',
        '[data-testid="seventh-chord"]',
        '[data-testid="chord-extensions"]'
      ]
    }
  }
];

export const ALL_VALIDATED_CASES = [
  ...CHORD_PROGRESSION_CASES,
  ...SCALE_ANALYSIS_CASES,
  ...MELODY_ANALYSIS_CASES,
  ...SINGLE_CHORD_CASES
];
