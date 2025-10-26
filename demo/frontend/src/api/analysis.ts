// Main play: Analysis API functions that talk to the backend
// This is where we make the magic happen - send chords, get back harmonic insights

import apiClient from './client';
import type { AnalysisRequest, AnalysisResponse, FileAnalysisResponse } from '../types/analysis';

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
