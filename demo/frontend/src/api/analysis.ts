// Analysis API functions that talk to the backend.
// One module exposes everything: chord analysis, file (notation) analysis,
// audio analysis, and the supporting key list.

import apiClient from './client';
import type { AnalysisRequest, AnalysisResponse, FileAnalysisResponse, KeysResponse } from '../types/analysis';
import type { AudioAnalysisResponse, AnalyzeAudioOptions } from '../types/audio';

export const analyzeChords = async (
  request: AnalysisRequest
): Promise<AnalysisResponse> => {
  // Fire off the analysis request to the backend
  const response = await apiClient.post<AnalysisResponse>('/api/analyze', request);
  return response.data;
};

// Big play: Upload music file for chord extraction and optional analysis
export const analyzeFile = async (
  file: File,
  options: {
    runAnalysis?: boolean;
    profile?: string;
  } = {}
): Promise<FileAnalysisResponse> => {
  // Setup: create FormData with file and options
  const formData = new FormData();
  formData.append('file', file);
  formData.append('run_analysis', options.runAnalysis ? 'true' : 'false');
  formData.append('profile', options.profile ?? 'classical');

  // Main event: send file to backend
  // Override the client's default application/json Content-Type - FormData needs multipart/form-data
  const response = await apiClient.post<FileAnalysisResponse>(
    '/api/analyze/file',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

// Victory lap: Fetch available musical keys from backend
export const fetchKeys = async (): Promise<KeysResponse> => {
  const response = await apiClient.get<KeysResponse>('/api/constants/keys');
  return response.data;
};

// Audio analysis — POST /api/analyze/audio with multipart form data.
// Backend accepts WAV directly; MP3/OGG/AAC need ffmpeg on the server PATH.
//
// `weights` lets advanced users override the ensemble weights per-approach
// (template_correlation, boundary_chords, bass_dominance, cadential). It's
// JSON-encoded into the form because FastAPI parses string Form params.
export const analyzeAudio = async (
  file: File,
  options: AnalyzeAudioOptions = {},
): Promise<AudioAnalysisResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  if (options.start != null) formData.append('start', String(options.start));
  if (options.end != null) formData.append('end', String(options.end));
  formData.append('show_details', options.showDetails ? 'true' : 'false');
  formData.append('key_detection', options.preset ?? 'default');
  if (options.weights && Object.keys(options.weights).length > 0) {
    formData.append('key_ensemble_weights', JSON.stringify(options.weights));
  }
  // Pass the chord-estimation tuning knobs through only when the caller set
  // them. Omitting these lets the library use its calibrated defaults.
  if (options.tonalBias != null) formData.append('tonal_bias', String(options.tonalBias));
  if (options.bassBonus != null) formData.append('bass_bonus', String(options.bassBonus));
  if (options.useBassChroma != null) {
    formData.append('use_bass_chroma', options.useBassChroma ? 'true' : 'false');
  }

  const response = await apiClient.post<AudioAnalysisResponse>(
    '/api/analyze/audio',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      // Audio analysis can take 10–30s on large files; bump past the default.
      timeout: 120_000,
    },
  );
  return response.data;
};
