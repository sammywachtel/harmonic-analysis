// Tab 2 — Notation upload. Drop a MusicXML/MIDI file; the engine extracts
// chords, runs the same analysis as Tab 1, and renders File Information +
// Extracted Chords + Analysis Summary banner + the full AnalysisResults tree.

import { useState } from 'react';
import { analyzeFile } from '../api/analysis';
import type { FileAnalysisResponse } from '../types/analysis';
import FileUploadZone from '../components/FileUploadZone';
import AnalysisResults from '../components/AnalysisResults';
import SectionCard from '../components/ui/SectionCard';
import Tag from '../components/ui/Tag';
import Eyebrow from '../components/ui/Eyebrow';

const ACCEPTED_TYPES = ['.xml', '.musicxml', '.mxl', '.mid', '.midi'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const Tab2 = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<FileAnalysisResponse | null>(null);

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      return 'File format not supported. Drop a MusicXML (.xml, .musicxml, .mxl) or MIDI (.mid, .midi) file.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum size: 10 MB.`;
    }
    return null;
  };

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

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setResults(null);
      const response = await analyzeFile(selectedFile, {
        runAnalysis: true,
        profile: 'classical',
      });
      setResults(response);
    } catch (err) {
      console.error('File analysis failed:', err);
      // FastAPI's validation errors come back as a list — surface the first
      // one helpfully instead of a generic "Failed to analyze".
      let errorMessage = 'Failed to analyze file. Please try again.';
      if (err && typeof err === 'object') {
        const e = err as { response?: { data?: { detail?: string | Array<{ loc?: string[]; msg: string }> } }; message?: string };
        if (e.response?.data?.detail) {
          const detail = e.response.data.detail;
          if (Array.isArray(detail) && detail.length > 0) {
            errorMessage = `${detail[0].loc?.slice(-1)[0] || 'Validation'}: ${detail[0].msg}`;
          } else if (typeof detail === 'string') {
            errorMessage = detail;
          }
        } else if (e.message) {
          errorMessage = e.message;
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setError(null);
    setResults(null);
    setLoading(false);
  };

  return (
    <div className="space-y-8">
      {/* Page intro */}
      <header>
        <h1 className="font-serif font-semibold text-4xl text-slate-900 tracking-tight">
          Analyze notation
        </h1>
        <p className="mt-2 text-slate-600 max-w-2xl text-base leading-relaxed">
          Drop a MusicXML or MIDI file. The engine extracts the chord progression and runs the
          full pattern analysis — same engine as manual entry, just fed from sheet music.
        </p>
      </header>

      {/* Upload + selected-file state. While analyzing, the form stays visible
          so you can swap files; only after results land do we hide it. */}
      {!results && (
        <SectionCard
          eyebrow="Upload"
          title="Drop a score"
          subtitle="MusicXML (.xml, .musicxml, .mxl) or MIDI (.mid, .midi), up to 10 MB"
        >
          <div className="space-y-5">
            {!selectedFile ? (
              <FileUploadZone
                onFileSelected={handleFileSelected}
                acceptedTypes={ACCEPTED_TYPES}
                maxSizeMB={10}
                disabled={loading}
              />
            ) : (
              <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/40">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0 flex-1">
                    <Eyebrow tone="primary">Selected file</Eyebrow>
                    <div className="mt-1 font-mono text-sm text-slate-900 truncate">
                      {selectedFile.name}
                    </div>
                    <div className="mt-1 text-xs text-slate-500 font-mono tabular-nums">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="text-sm text-slate-600 hover:text-slate-900 underline"
                    disabled={loading}
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading || !selectedFile}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition shadow-sm"
            >
              {loading ? 'Analyzing file…' : 'Analyze file'}
            </button>

            <div className="text-xs text-slate-500 space-y-1.5">
              <Eyebrow tone="slate">How it works</Eyebrow>
              <ol className="list-decimal list-inside space-y-1 mt-1.5">
                <li>Drop a MusicXML or MIDI score above.</li>
                <li>The engine extracts a chord progression from the notation.</li>
                <li>Pattern analysis identifies the key, Roman numerals, and stylistic patterns.</li>
                <li>You see the result with confidence scores and educational notes.</li>
              </ol>
            </div>
          </div>
        </SectionCard>
      )}

      {/* Error banner */}
      {error && (
        <SectionCard
          eyebrow="Error"
          title="Couldn't analyze that file"
          className="border-rose-200 bg-rose-50/50"
        >
          <p className="text-sm text-rose-800">{error}</p>
        </SectionCard>
      )}

      {/* Results: File Info → Extracted Chords → AnalysisResults → Reset */}
      {results && (
        <div className="space-y-8">
          <SectionCard eyebrow="File" title="File information">
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
              {results.metadata?.title && (
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">Title</dt>
                  <dd className="text-slate-900 mt-0.5">{String(results.metadata.title)}</dd>
                </div>
              )}
              {results.metadata?.composer && (
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">Composer</dt>
                  <dd className="text-slate-900 mt-0.5">{String(results.metadata.composer)}</dd>
                </div>
              )}
              <div>
                <dt className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">File type</dt>
                <dd className="mt-0.5">
                  <Tag tone={results.is_midi ? 'indigo' : 'primary'}>
                    {results.is_midi ? 'MIDI' : 'MusicXML'}
                  </Tag>
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">Measures</dt>
                <dd className="text-slate-900 mt-0.5 font-mono tabular-nums">{results.measure_count}</dd>
              </div>
              {results.key_hint && (
                <div>
                  <dt className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">Detected key</dt>
                  <dd className="text-slate-900 mt-0.5 font-serif italic">{results.key_hint}</dd>
                </div>
              )}
            </dl>
            {results.truncated_for_display && (
              <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900">
                Display limited to the first portion of the file for performance.
              </div>
            )}
          </SectionCard>

          {/* Extracted chord pills — mono grid per design spec. */}
          <SectionCard
            eyebrow="Extracted"
            title={`Extracted chords · ${results.chord_symbols?.length ?? 0}`}
            subtitle="Chord symbols pulled from the notation"
          >
            {results.chord_symbols && results.chord_symbols.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {results.chord_symbols.slice(0, 50).map((chord, idx) => (
                  <span
                    key={idx}
                    className="inline-flex bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-md font-mono text-sm text-slate-800"
                  >
                    {chord}
                  </span>
                ))}
                {results.chord_symbols.length > 50 && (
                  <span className="inline-flex items-center text-xs text-slate-500 px-2 py-1.5 font-mono tabular-nums">
                    + {results.chord_symbols.length - 50} more
                  </span>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No chords were extracted from this file.</p>
            )}
          </SectionCard>

          {/* Full analysis tree (re-uses Tab 1's machinery). */}
          {results.analysis_result && (
            <AnalysisResults
              results={results.analysis_result}
              chords={results.chord_symbols ?? []}
            />
          )}

          {/* Reset CTA */}
          <button
            type="button"
            onClick={handleReset}
            className="w-full bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-3 px-6 rounded-lg transition border border-slate-200"
          >
            Analyze another file
          </button>
        </div>
      )}
    </div>
  );
};

export default Tab2;
