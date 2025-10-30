// Tab 1: Manual chord entry - the main interface for testing the analysis engine
// Users enter chords, pick a key/profile, hit analyze, and see the results

import { useState, useEffect } from 'react';
import { analyzeChords, fetchKeys } from '../api/analysis';
import type { AnalysisResponse } from '../types/analysis';
import AnalysisResults from '../components/AnalysisResults';
import { isDemoMode } from '../config/environment';

const Tab1 = () => {
  // State management - form inputs, loading, results, errors
  const [chordsInput, setChordsInput] = useState('');
  const [selectedKey, setSelectedKey] = useState('');
  const [selectedProfile, setSelectedProfile] = useState('classical');
  const [showEducational, setShowEducational] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [analyzedChords, setAnalyzedChords] = useState<string[]>([]);

  const demoMode = isDemoMode();

  // Key options for the dropdown - fetched from backend on mount
  const [keyOptions, setKeyOptions] = useState<Array<{ value: string; label: string }>>([
    { value: '', label: 'Auto-detect' },
  ]);

  // Opening move: fetch available keys when component mounts
  useEffect(() => {
    const loadKeys = async () => {
      try {
        const keysData = await fetchKeys();
        console.log('Keys response:', keysData); // Debug what we got back

        // Guard: make sure we have the keys array
        if (!keysData || !keysData.keys || !Array.isArray(keysData.keys)) {
          console.error('Invalid keys response - expected {keys: string[]}:', keysData);
          return;
        }

        // Build dropdown options from API response
        const options = [
          { value: '', label: 'Auto-detect' },
          ...keysData.keys.map((key) => ({
            value: key,
            label: key,
          })),
        ];
        setKeyOptions(options);
      } catch (err) {
        console.error('Failed to load keys:', err);
        // Keep the default "Auto-detect" option if fetch fails
      }
    };

    loadKeys();
  }, []);

  // Profile options - different analysis approaches
  const profileOptions = [
    { value: 'classical', label: 'Classical' },
    { value: 'jazz', label: 'Jazz' },
    { value: 'pop', label: 'Pop' },
    { value: 'modal', label: 'Modal' },
  ];

  // Main play: handle the analyze button click
  const handleAnalyze = async () => {
    // Guard clause: need some chords to analyze
    if (!chordsInput.trim()) {
      setError('Please enter at least one chord');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResults(null);

      // Parse chords - split by commas, spaces, or newlines
      const chords = chordsInput
        .split(/[,\s\n]+/)
        .map((c) => c.trim())
        .filter((c) => c.length > 0);

      // Fire off the API request
      const response = await analyzeChords({
        chords,
        key: selectedKey || undefined,
        profile: selectedProfile,
        include_educational: showEducational,
      });

      setResults(response);
      setAnalyzedChords(chords);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Failed to analyze progression. Please check your input and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Quick examples to help users get started
  const loadExample = (example: string) => {
    setChordsInput(example);
    setError(null);
    setResults(null);
  };

  return (
    <div className="space-y-6">
      {/* Demo mode: show Python code example */}
      {demoMode && (
        <div className="bg-slate-100 border border-slate-300 rounded-lg p-4">
          <h3 className="font-semibold text-slate-900 mb-2">Python API Example</h3>
          <pre className="text-sm text-slate-800 bg-white p-3 rounded overflow-x-auto">
{`from harmonic_analysis.services import PatternAnalysisService

service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(
    ['C', 'F', 'G', 'C'],
    profile="classical"
)
print(f"Key: {result.primary.key}")
print(f"Roman numerals: {result.primary.roman_numerals}")`}
          </pre>
        </div>
      )}

      {/* Input form - the main interface */}
      <div className="bg-white border border-slate-300 rounded-lg p-6 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900 mb-4">Enter Chord Progression</h2>

        <div className="space-y-4">
          {/* Chords input - the most important field */}
          <div>
            <label htmlFor="chords" className="block text-sm font-medium text-slate-700 mb-2">
              Chords (comma or space separated)
            </label>
            <textarea
              id="chords"
              value={chordsInput}
              onChange={(e) => setChordsInput(e.target.value)}
              placeholder="Example: C, F, G, C"
              rows={4}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              aria-describedby="chords-help"
            />
            <p id="chords-help" className="mt-1 text-sm text-slate-500">
              Enter chord symbols like C, Dm, G7, Fmaj7, etc.
            </p>
          </div>

          {/* Quick examples - help users get started fast */}
          <div>
            <p className="text-sm font-medium text-slate-700 mb-2">Quick Examples:</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => loadExample('C, Am, F, G')}
                className="text-sm bg-slate-200 hover:bg-slate-300 px-3 py-1 rounded transition"
              >
                I-vi-IV-V
              </button>
              <button
                onClick={() => loadExample('Dm, G7, Cmaj7')}
                className="text-sm bg-slate-200 hover:bg-slate-300 px-3 py-1 rounded transition"
              >
                ii-V-I
              </button>
              <button
                onClick={() => loadExample('C, G, Am, F')}
                className="text-sm bg-slate-200 hover:bg-slate-300 px-3 py-1 rounded transition"
              >
                Pop Progression
              </button>
            </div>
          </div>

          {/* Key hint dropdown */}
          <div>
            <label htmlFor="key" className="block text-sm font-medium text-slate-700 mb-2">
              Key Hint (optional)
            </label>
            <select
              id="key"
              value={selectedKey}
              onChange={(e) => setSelectedKey(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {keyOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-slate-500">
              Leave as "Auto-detect" to let the engine figure it out
            </p>
          </div>

          {/* Profile dropdown */}
          <div>
            <label htmlFor="profile" className="block text-sm font-medium text-slate-700 mb-2">
              Analysis Profile
            </label>
            <select
              id="profile"
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {profileOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-slate-500">
              Different profiles emphasize different harmonic features
            </p>
          </div>

          {/* Big play: Educational content toggle */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="show-educational"
              checked={showEducational}
              onChange={(e) => setShowEducational(e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
            />
            <label htmlFor="show-educational" className="ml-2 block text-sm text-slate-700">
              Show educational content
            </label>
          </div>

          {/* Analyze button - the big moment */}
          <button
            onClick={handleAnalyze}
            disabled={loading || !chordsInput.trim()}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-400 text-white font-semibold py-3 px-6 rounded-lg transition shadow-sm"
          >
            {loading ? 'Analyzing...' : 'Analyze Progression'}
          </button>
        </div>
      </div>

      {/* Error display - clear and helpful */}
      {error && (
        <div className="bg-error-50 border-l-4 border-error-500 p-4 rounded">
          <p className="text-error-800">{error}</p>
        </div>
      )}

      {/* Results display - the payoff */}
      {results && <AnalysisResults results={results} showEducational={showEducational} chords={analyzedChords} />}
    </div>
  );
};

export default Tab1;
