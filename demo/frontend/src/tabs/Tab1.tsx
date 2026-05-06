// Tab 1 — Manual entry. The user types chord symbols, optionally pins a key
// and a style profile, and the engine returns a full multi-profile reading.
//
// Layout (per design README):
//   1. Page intro (serif h1 + slate subtitle)
//   2. Input panel (SectionCard) — chord textarea, examples, key + profile,
//      educational toggle, analyze button
//   3. Python API example (SectionCard, demo mode only)
//   4. Error banner (rose-toned SectionCard)
//   5. AnalysisResults — hero card + Roman score + patterns + ...

import { useState, useEffect } from 'react';
import { analyzeChords, fetchKeys } from '../api/analysis';
import type { AnalysisResponse } from '../types/analysis';
import AnalysisResults from '../components/AnalysisResults';
import SectionCard from '../components/ui/SectionCard';
import Tag from '../components/ui/Tag';
import { isDemoMode } from '../config/environment';

const Tab1 = () => {
  const [chordsInput, setChordsInput] = useState('');
  const [selectedKey, setSelectedKey] = useState('');
  const [selectedProfile, setSelectedProfile] = useState('');
  const [showEducational, setShowEducational] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [analyzedChords, setAnalyzedChords] = useState<string[]>([]);

  const demoMode = isDemoMode();

  const [keyOptions, setKeyOptions] = useState<Array<{ value: string; label: string }>>([
    { value: '', label: 'Auto-detect' },
  ]);

  // Fetch the key dropdown options once on mount; fall back to "Auto-detect" only.
  useEffect(() => {
    const loadKeys = async () => {
      try {
        const keysData = await fetchKeys();
        if (!keysData || !keysData.keys || !Array.isArray(keysData.keys)) {
          console.error('Invalid keys response - expected {keys: string[]}:', keysData);
          return;
        }
        setKeyOptions([
          { value: '', label: 'Auto-detect' },
          ...keysData.keys.map((key) => ({ value: key, label: key })),
        ]);
      } catch (err) {
        console.error('Failed to load keys:', err);
      }
    };
    loadKeys();
  }, []);

  // Profile options: empty value = full multi-profile breakdown.
  const profileOptions = [
    { value: '',          label: 'All styles (no focus)' },
    { value: 'classical', label: 'Classical' },
    { value: 'jazz',      label: 'Jazz' },
    { value: 'pop',       label: 'Pop' },
    { value: 'modal',     label: 'Modal' },
  ];

  const handleAnalyze = async () => {
    if (!chordsInput.trim()) {
      setError('Please enter at least one chord');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setResults(null);
      const chords = chordsInput.split(/[,\s\n]+/).map((c) => c.trim()).filter(Boolean);
      const response = await analyzeChords({
        chords,
        key: selectedKey || undefined,
        profile: selectedProfile || undefined,
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

  const loadExample = (example: string) => {
    setChordsInput(example);
    setError(null);
    setResults(null);
  };

  const inputClass =
    'w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent transition';

  return (
    <div className="space-y-8">
      {/* Page intro */}
      <header>
        <h1 className="font-serif font-semibold text-4xl text-slate-900 tracking-tight">
          Manual entry
        </h1>
        <p className="mt-2 text-slate-600 max-w-2xl text-base leading-relaxed">
          Type a chord progression. The engine returns a key estimate, Roman numerals, and a
          full pattern analysis — with optional Bernstein-style educational explanations.
        </p>
      </header>

      {/* Input panel */}
      <SectionCard
        eyebrow="Input"
        title="Chord progression"
        subtitle="Use letter names; spaces, commas, or newlines all separate chords"
      >
        <div className="space-y-5">
          <div>
            <label htmlFor="chords" className="block text-sm font-medium text-slate-700 mb-2">
              Chords
            </label>
            <textarea
              id="chords"
              value={chordsInput}
              onChange={(e) => setChordsInput(e.target.value)}
              placeholder="Example: C  Am  F  G"
              rows={3}
              className={`${inputClass} font-mono`}
              aria-describedby="chords-help"
            />
            <p id="chords-help" className="mt-1.5 text-xs text-slate-500">
              Chord symbols like C, Dm, G7, Fmaj7, B♭/D, etc.
            </p>
          </div>

          {/* Quick example buttons */}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500 mb-2">
              Quick examples
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => loadExample('C  Am  F  G')}
                className="text-sm bg-slate-50 hover:bg-primary-50 hover:text-primary-800 hover:border-primary-200 border border-slate-200 px-3 py-1.5 rounded-md transition font-mono text-slate-700"
              >
                I – vi – IV – V
              </button>
              <button
                type="button"
                onClick={() => loadExample('Dm  G7  Cmaj7')}
                className="text-sm bg-slate-50 hover:bg-primary-50 hover:text-primary-800 hover:border-primary-200 border border-slate-200 px-3 py-1.5 rounded-md transition font-mono text-slate-700"
              >
                ii – V – I
              </button>
              <button
                type="button"
                onClick={() => loadExample('C  G  Am  F')}
                className="text-sm bg-slate-50 hover:bg-primary-50 hover:text-primary-800 hover:border-primary-200 border border-slate-200 px-3 py-1.5 rounded-md transition font-mono text-slate-700"
              >
                I – V – vi – IV
              </button>
            </div>
          </div>

          {/* Key + Profile in a 2-col grid on wider screens */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="key" className="block text-sm font-medium text-slate-700 mb-2">
                Key hint <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <select
                id="key"
                value={selectedKey}
                onChange={(e) => setSelectedKey(e.target.value)}
                className={inputClass}
              >
                {keyOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <p className="mt-1.5 text-xs text-slate-500">
                Leave on Auto-detect to let the engine choose.
              </p>
            </div>

            <div>
              <label htmlFor="profile" className="block text-sm font-medium text-slate-700 mb-2">
                Profile focus <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <select
                id="profile"
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                className={inputClass}
                data-testid="profile-selector"
              >
                {profileOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <p className="mt-1.5 text-xs text-slate-500">
                Emphasize one style, or leave empty for the full multi-profile breakdown.
              </p>
            </div>
          </div>

          {/* Educational toggle */}
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              id="show-educational"
              checked={showEducational}
              onChange={(e) => setShowEducational(e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded"
            />
            <span className="text-sm text-slate-700">Show educational explanations on patterns</span>
          </label>

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading || !chordsInput.trim()}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition shadow-sm"
          >
            {loading ? 'Analyzing…' : 'Analyze progression'}
          </button>
        </div>
      </SectionCard>

      {/* Demo mode: Python API equivalent */}
      {demoMode && (
        <SectionCard
          eyebrow="Python API"
          title="Same call from your code"
          subtitle="The library exposes the same engine under a small async surface"
          action={<Tag tone="slate">demo</Tag>}
        >
          <pre className="text-xs sm:text-sm font-mono text-slate-800 bg-slate-50 p-4 rounded-lg overflow-x-auto border border-slate-200">
{`from harmonic_analysis.services import PatternAnalysisService

service = PatternAnalysisService()
result = await service.analyze_with_patterns_async(
    ['C', 'Am', 'F', 'G'],
    profile="classical"
)
print(result.primary.key_signature)
print(result.primary.roman_numerals)`}
          </pre>
        </SectionCard>
      )}

      {/* Error banner */}
      {error && (
        <SectionCard
          eyebrow="Error"
          title="Couldn't analyze that"
          className="border-rose-200 bg-rose-50/50"
        >
          <p className="text-sm text-rose-800">{error}</p>
        </SectionCard>
      )}

      {/* Results */}
      {results && (
        <AnalysisResults
          results={results}
          showEducational={showEducational}
          chords={analyzedChords}
        />
      )}
    </div>
  );
};

export default Tab1;
