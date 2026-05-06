// Smoke test for the audio adapter. Confirms it correctly:
//   1. Tags chord function from chord_label + tonic + mode
//   2. Picks up borrowed labels when local.borrowed_tones is empty
//   3. Sorts the 24-key histogram by score desc
//   4. Sets keysMatch when global == local

import { describe, it, expect } from 'vitest';
import { enrichAudioResult, formatTime } from '../audioAdapter';
import type { AudioAnalysisResponse } from '../../types/audio';

const makeResponse = (overrides: Partial<AudioAnalysisResponse> = {}): AudioAnalysisResponse => ({
  global: { tonic: 'C', mode: 'Ionian', key_signature: '0 sharps', confidence: 0.9 },
  local: {
    tonic: 'C',
    mode: 'Ionian',
    key_signature: '0 sharps',
    confidence: 0.9,
    region_type: 'stable',
    region_confidence: 0.95,
    borrowed_tones: [],
  },
  analysis: { cadence_detected: true, cadence_strength: 0.82 },
  chord_progression: [
    { start_time: 0,   end_time: 2,  chord_label: 'C',  confidence: 0.95, is_diatonic: true  },
    { start_time: 2,   end_time: 4,  chord_label: 'F',  confidence: 0.91, is_diatonic: true  },
    { start_time: 4,   end_time: 6,  chord_label: 'G',  confidence: 0.93, is_diatonic: true  },
    { start_time: 6,   end_time: 8,  chord_label: 'Eb', confidence: 0.65, is_diatonic: false },
  ],
  segment: { start: 0, end: 8 },
  ...overrides,
});

describe('audioAdapter.enrichAudioResult', () => {
  it('classifies chord function from root pitch class', () => {
    const out = enrichAudioResult(makeResponse());
    expect(out.chord_progression[0].function).toBe('tonic');       // C in C major
    expect(out.chord_progression[1].function).toBe('predominant'); // F (IV)
    expect(out.chord_progression[2].function).toBe('dominant');    // G (V)
    expect(out.chord_progression[3].function).toBe('chromatic');   // Eb non-diatonic
  });

  it('falls back to chord-progression scan when local.borrowed_tones is empty', () => {
    const out = enrichAudioResult(makeResponse());
    expect(out.borrowedLabels).toContain('Eb');
  });

  it('respects backend-provided borrowed_tones when present', () => {
    const out = enrichAudioResult(
      makeResponse({
        local: {
          tonic: 'C', mode: 'Ionian', key_signature: '0 sharps', confidence: 0.9,
          region_type: 'stable', region_confidence: 0.95,
          borrowed_tones: ['Eb (♭3)', 'Ab (♭6)'],
        },
      }),
    );
    expect(out.borrowedLabels).toEqual(['Eb (♭3)', 'Ab (♭6)']);
  });

  it('sorts the 24-key histogram by score descending when key_analysis_details present', () => {
    const out = enrichAudioResult(
      makeResponse({
        key_analysis_details: {
          approaches: [],
          synthesis: {
            method: 'weighted_sum',
            winner: { tonic: 'C', mode: 'Ionian', key_signature: '0 sharps', confidence: 0.9 },
            runner_up: null,
            margin: 0.1,
            key_score_table: { 'C Ionian': 2.4, 'A Aeolian': 1.9, 'G Ionian': 1.7 },
          },
          modulations: null,
        },
      }),
    );

    expect(out.analysis.key_scores.length).toBe(3);
    expect(out.analysis.key_scores[0].tonic).toBe('C');
    expect(out.analysis.key_scores[0].score).toBe(2.4);
    expect(out.analysis.key_scores[1].score).toBeLessThan(out.analysis.key_scores[0].score);
  });

  it('flags keysMatch when global and local agree', () => {
    expect(enrichAudioResult(makeResponse()).keysMatch).toBe(true);
  });

  it('shifts chord timestamps by segment.start so consumers see absolute file time', () => {
    // Backend returns segment-relative timestamps; we want absolute file time
    // downstream so Timeline + ChordProgression + audio playback all agree.
    const out = enrichAudioResult(
      makeResponse({
        segment: { start: 30, end: 38 },
        chord_progression: [
          { start_time: 0, end_time: 2, chord_label: 'C',  confidence: 0.9, is_diatonic: true },
          { start_time: 2, end_time: 4, chord_label: 'F',  confidence: 0.9, is_diatonic: true },
        ],
      }),
    );
    expect(out.chord_progression[0].start_time).toBe(30);
    expect(out.chord_progression[0].end_time).toBe(32);
    expect(out.chord_progression[1].start_time).toBe(32);
    expect(out.chord_progression[1].end_time).toBe(34);
  });

  it('leaves timestamps untouched when segment starts at 0', () => {
    const out = enrichAudioResult(makeResponse());
    expect(out.chord_progression[0].start_time).toBe(0);
    expect(out.chord_progression[1].start_time).toBe(2);
  });

  it('clears keysMatch when global and local diverge', () => {
    const out = enrichAudioResult(
      makeResponse({
        local: {
          tonic: 'A', mode: 'Aeolian', key_signature: '0 sharps', confidence: 0.85,
          region_type: 'modulation', region_confidence: 0.7, borrowed_tones: [],
        },
      }),
    );
    expect(out.keysMatch).toBe(false);
  });
});

describe('formatTime', () => {
  it('formats whole minutes', () => {
    expect(formatTime(0)).toBe('0:00');
    expect(formatTime(59)).toBe('0:59');
    expect(formatTime(60)).toBe('1:00');
    expect(formatTime(125)).toBe('2:05');
  });

  it('handles invalid inputs gracefully', () => {
    expect(formatTime(NaN)).toBe('0:00');
    expect(formatTime(-1)).toBe('0:00');
  });
});
