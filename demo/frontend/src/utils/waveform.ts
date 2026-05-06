// Browser-side waveform peak extraction. Decodes the user's audio file via
// the Web Audio API and downsamples one channel to a fixed-length array of
// max-amplitude peaks suitable for canvas rendering.
//
// We use the Web Audio API instead of asking the backend for peaks because:
//   1. The browser already decodes the same formats the backend accepts (WAV,
//      MP3, OGG via the platform's codec).
//   2. ~800 peaks for a 3-minute file decode in <100ms on commodity hardware,
//      so the UI still feels instant.
//   3. No new endpoint, no megabytes of waveform data over the wire.

const DEFAULT_PEAK_COUNT = 800;

/**
 * Read the file as an ArrayBuffer, decode through AudioContext, and downsample
 * channel 0 to `samples` peaks. Each peak is the max-abs amplitude across its
 * window of source samples — what you want for a canvas waveform display.
 *
 * Returns peaks in [0, 1]. Returns an empty array if decoding fails so callers
 * can render a blank track instead of crashing.
 */
export const extractPeaks = async (
  file: File,
  samples: number = DEFAULT_PEAK_COUNT,
): Promise<{ peaks: number[]; durationSec: number; sampleRate: number; channels: number }> => {
  const empty = { peaks: [], durationSec: 0, sampleRate: 0, channels: 0 };

  try {
    const arrayBuffer = await file.arrayBuffer();

    // Some browsers still expose webkitAudioContext rather than AudioContext.
    type CtxCtor = typeof AudioContext;
    const Ctx: CtxCtor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: CtxCtor }).webkitAudioContext;
    if (!Ctx) return empty;

    const ctx = new Ctx();
    try {
      // decodeAudioData returns a Promise in modern browsers; the callback form
      // is the legacy fallback. We use the Promise form.
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
      const channelData = audioBuffer.getChannelData(0);
      const blockSize = Math.max(1, Math.floor(channelData.length / samples));
      const peaks: number[] = new Array(samples).fill(0);

      for (let i = 0; i < samples; i++) {
        const blockStart = i * blockSize;
        const blockEnd = Math.min(channelData.length, blockStart + blockSize);
        let maxAbs = 0;
        for (let j = blockStart; j < blockEnd; j++) {
          const v = Math.abs(channelData[j]);
          if (v > maxAbs) maxAbs = v;
        }
        peaks[i] = Math.min(1, maxAbs);
      }

      return {
        peaks,
        durationSec: audioBuffer.duration,
        sampleRate: audioBuffer.sampleRate,
        channels: audioBuffer.numberOfChannels,
      };
    } finally {
      // Closing the context releases the underlying audio engine resources.
      // Some older Safari builds throw on close() — swallow if so.
      try { await ctx.close(); } catch { /* noop */ }
    }
  } catch (err) {
    console.warn('[waveform] decodeAudioData failed:', err);
    return empty;
  }
};
