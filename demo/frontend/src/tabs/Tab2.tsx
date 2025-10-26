// Tab 2: File upload - upload MusicXML or MIDI files for automatic chord extraction
// This is the "I have sheet music" workflow - upload and let the engine do the work

import { useState } from 'react';
import { analyzeFile } from '../api/analysis';
import type { FileAnalysisResponse } from '../types/analysis';
import FileUploadZone from '../components/FileUploadZone';
import AnalysisResults from '../components/AnalysisResults';

const Tab2 = () => {
  // State management - following Tab1 pattern exactly
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<FileAnalysisResponse | null>(null);

  // Client-side validation constants
  const ACCEPTED_TYPES = ['.xml', '.musicxml', '.mxl', '.mid', '.midi'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  // Guard clause: validate file type and size
  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!ACCEPTED_TYPES.includes(ext)) {
      return `File format not supported. Please upload MusicXML (.xml, .musicxml, .mxl) or MIDI (.mid, .midi) files.`;
    }

    if (file.size > MAX_FILE_SIZE) {
      return `File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum size: 10MB`;
    }

    return null; // Valid file
  };

  // Main play: handle file selection from upload zone
  const handleFileSelected = (file: File) => {
    const validationError = validateFile(file);

    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      setResults(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
    setResults(null);
  };

  // Big play: analyze the selected file
  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResults(null);

      // Fire off the file upload and analysis
      const response = await analyzeFile(selectedFile, {
        runAnalysis: true,
        profile: 'classical',
      });

      setResults(response);
    } catch (err) {
      console.error('File analysis failed:', err);

      // Extract helpful error message from backend
      let errorMessage = 'Failed to analyze file. Please try again.';
      if (err && typeof err === 'object') {
        const error = err as { response?: { data?: { detail?: string | Array<{ loc?: string[]; msg: string }> } }; message?: string };
        if (error.response?.data?.detail) {
          const detail = error.response.data.detail;
          // Handle FastAPI validation errors (array of objects)
          if (Array.isArray(detail) && detail.length > 0) {
            // Extract first error message: "run_analysis: Input should be a valid boolean"
            const firstError = detail[0];
            errorMessage = `${firstError.loc?.slice(-1)[0] || 'Validation'}: ${firstError.msg}`;
          } else if (typeof detail === 'string') {
            // Handle string detail (other error types)
            errorMessage = detail;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Reset workflow: start over with a new file
  const handleReset = () => {
    setSelectedFile(null);
    setError(null);
    setResults(null);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Main upload interface - show this when no results yet */}
      {!results && (
        <div className="bg-white border border-gray-300 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Upload Music File</h2>

          <div className="space-y-4">
            {/* File upload zone - drag-and-drop or click to browse */}
            <FileUploadZone
              onFileSelected={handleFileSelected}
              acceptedTypes={ACCEPTED_TYPES}
              maxSizeMB={10}
              disabled={loading}
            />

            {/* Show selected file info */}
            {selectedFile && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-blue-900">Selected File</p>
                    <p className="text-sm text-blue-800 mt-1">{selectedFile.name}</p>
                    <p className="text-xs text-blue-600 mt-1">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    disabled={loading}
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}

            {/* Analyze button - the main action */}
            <button
              onClick={handleAnalyze}
              disabled={loading || !selectedFile}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition shadow-sm"
            >
              {loading ? 'Analyzing File...' : 'Analyze File'}
            </button>

            {/* Help text */}
            <div className="bg-gray-50 border border-gray-200 rounded p-4">
              <h3 className="font-semibold text-gray-900 mb-2">How it works</h3>
              <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
                <li>Upload a MusicXML or MIDI file</li>
                <li>The system extracts chords automatically</li>
                <li>Harmonic analysis identifies keys and patterns</li>
                <li>View results with confidence scores</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Error display - clear and helpful */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <div className="flex items-start">
            <div className="flex-1">
              <p className="text-red-800 font-semibold">Error</p>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results display - the payoff */}
      {results && (
        <div className="space-y-6">
          {/* File metadata section */}
          <div className="bg-white border border-gray-300 rounded-lg p-6 shadow-sm">
            <h3 className="text-xl font-bold text-gray-900 mb-4">File Information</h3>

            <div className="grid grid-cols-2 gap-4">
              {results.metadata?.title && (
                <div>
                  <span className="text-sm font-semibold text-gray-700">Title: </span>
                  <span className="text-sm text-gray-900">{results.metadata.title}</span>
                </div>
              )}
              {results.metadata?.composer && (
                <div>
                  <span className="text-sm font-semibold text-gray-700">Composer: </span>
                  <span className="text-sm text-gray-900">{results.metadata.composer}</span>
                </div>
              )}
              <div>
                <span className="text-sm font-semibold text-gray-700">File Type: </span>
                <span className="text-sm text-gray-900">{results.is_midi ? 'MIDI' : 'MusicXML'}</span>
              </div>
              <div>
                <span className="text-sm font-semibold text-gray-700">Measures: </span>
                <span className="text-sm text-gray-900">{results.measure_count}</span>
              </div>
              {results.key_hint && (
                <div>
                  <span className="text-sm font-semibold text-gray-700">Detected Key: </span>
                  <span className="text-sm text-gray-900">{results.key_hint}</span>
                </div>
              )}
            </div>

            {results.truncated_for_display && (
              <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-sm text-yellow-800">
                  Note: Display limited to first portion of file for performance
                </p>
              </div>
            )}
          </div>

          {/* Extracted chords section */}
          <div className="bg-white border border-gray-300 rounded-lg p-6 shadow-sm">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Extracted Chords</h3>

            {results.chord_symbols && results.chord_symbols.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {results.chord_symbols.slice(0, 50).map((chord, idx) => (
                  <span
                    key={idx}
                    className="inline-block bg-gray-100 text-gray-800 px-3 py-1 rounded font-mono text-sm"
                  >
                    {chord}
                  </span>
                ))}
                {results.chord_symbols.length > 50 && (
                  <span className="inline-block text-gray-600 px-3 py-1 text-sm">
                    ... and {results.chord_symbols.length - 50} more
                  </span>
                )}
              </div>
            ) : (
              <p className="text-gray-600">No chords extracted</p>
            )}
          </div>

          {/* Analysis results - reuse AnalysisResults component if available */}
          {results.analysis_result && (
            <AnalysisResults results={results.analysis_result} />
          )}

          {/* Reset button - analyze another file */}
          <button
            onClick={handleReset}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-3 px-6 rounded-lg transition"
          >
            Analyze Another File
          </button>
        </div>
      )}
    </div>
  );
};

export default Tab2;
