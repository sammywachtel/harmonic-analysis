// Audio playback controller — single source of truth for currentTime, play
// state, and seek/toggle commands. Lives outside any single component so the
// timeline waveform AND the chord-progression table can subscribe to the
// same playhead and stay in lockstep during playback.
//
// Keyboard shortcuts (Space, ←, →) are handled here too: they need to read
// `audio.currentTime` directly (not the React state) to avoid re-binding the
// listener on every `timeupdate` tick.

import { useCallback, useEffect, useRef, useState } from 'react';

interface UseAudioPlayerOptions {
  /** Object URL or remote URL for the file. When this changes, internal
   *  state resets to zero (or whatever localStorage remembered). */
  audioSrc?: string;
  /** Suffix for the localStorage key, so multiple players on the same page
   *  don't trample each other's persisted positions. */
  storageKey: string;
  /** Visible segment range in absolute file seconds. seek() clamps to this,
   *  togglePlay() snaps into it if currentTime is outside. */
  segmentStart?: number;
  segmentEnd?: number;
  /** Maximum value seek() will clamp to. Usually the file duration. */
  maxTime: number;
  /** When true, register window keydown shortcuts (Space, ←, →). */
  enableKeyboardShortcuts?: boolean;
}

export interface AudioPlayerHandle {
  /** Attach this ref to the actual <audio> element. */
  audioRef: React.RefObject<HTMLAudioElement | null>;
  currentTime: number;
  isPlaying: boolean;
  togglePlay: () => void;
  seek: (timeSec: number) => void;
}

const SCAN_STEP = 5;
const SCAN_STEP_BIG = 15;

const isEditable = (el: EventTarget | null): boolean => {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (el.isContentEditable) return true;
  return false;
};

export const useAudioPlayer = ({
  audioSrc,
  storageKey,
  segmentStart = 0,
  segmentEnd,
  maxTime,
  enableKeyboardShortcuts = true,
}: UseAudioPlayerOptions): AudioPlayerHandle => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lsKey = `audio-timeline-${storageKey}`;

  const segStart = Math.max(0, Math.min(maxTime, segmentStart));
  const segEnd = Math.max(segStart, Math.min(maxTime, segmentEnd ?? maxTime));

  const [currentTime, setCurrentTime] = useState<number>(() => {
    const stored = typeof window !== 'undefined' ? window.localStorage.getItem(lsKey) : null;
    return stored ? parseFloat(stored) || 0 : 0;
  });
  const [isPlaying, setIsPlaying] = useState(false);

  // Wire up audio element events for currentTime + play state.
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime = () => setCurrentTime(audio.currentTime);
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('ended', onPause);
    return () => {
      audio.removeEventListener('timeupdate', onTime);
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('ended', onPause);
    };
  }, [audioSrc]);

  // Persist current time. The cadence of timeupdate (~4Hz) is fine — no need
  // for explicit throttling.
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(lsKey, String(currentTime));
    }
  }, [currentTime, lsKey]);

  const seek = useCallback((timeSec: number) => {
    const audio = audioRef.current;
    const clamped = Math.max(segStart, Math.min(segEnd, timeSec));
    if (audio) audio.currentTime = clamped;
    setCurrentTime(clamped);
  }, [segStart, segEnd]);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      // If we're about to start playback and currentTime sits outside the
      // visible segment, jump to segStart first. Without this the user hits
      // Space, audio plays from t=0 at the start of the file, but the
      // playhead never shows up because it's outside the zoomed view.
      if (audio.currentTime < segStart - 0.01 || audio.currentTime > segEnd + 0.01) {
        audio.currentTime = segStart;
        setCurrentTime(segStart);
      }
      audio.play().catch((e) => console.warn('audio play failed:', e));
    } else {
      audio.pause();
    }
  }, [segStart, segEnd]);

  // Global keyboard shortcuts: Space, ←, → (Shift for ±15s).
  useEffect(() => {
    if (!enableKeyboardShortcuts || !audioSrc) return;

    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (isEditable(e.target)) return;

      const audio = audioRef.current;
      if (!audio) return;

      switch (e.key) {
        case ' ':
        case 'Spacebar': {
          e.preventDefault();
          togglePlay();
          break;
        }
        case 'ArrowRight': {
          e.preventDefault();
          const step = e.shiftKey ? SCAN_STEP_BIG : SCAN_STEP;
          seek(audio.currentTime + step);
          break;
        }
        case 'ArrowLeft': {
          e.preventDefault();
          const step = e.shiftKey ? SCAN_STEP_BIG : SCAN_STEP;
          seek(audio.currentTime - step);
          break;
        }
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [audioSrc, togglePlay, seek, enableKeyboardShortcuts]);

  return { audioRef, currentTime, isPlaying, togglePlay, seek };
};
