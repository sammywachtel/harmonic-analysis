// Tab 1 — Manual entry. The user types chord symbols, optionally pins a key
// and a style profile, and the engine returns a full multi-profile reading.
//
// Layout (per design README — "Workbench" / Proposal D):
//   - Fixed two-column frame that fills the viewport below the app header/tabs.
//   - LEFT (340px, fixed): InputPanel — title strip, scrollable form body,
//     pinned action footer with Analyze button + "View as Python" link.
//   - RIGHT (flex-1, scrolls): error banner (if any), then either an empty
//     state placeholder or the full AnalysisResults block.
//
// The page-level Python "SectionCard" that used to sit inline is gone — that
// content now lives in CodeModal, opened from the View-as-Python link.

import { useState, useEffect } from 'react';
import { analyzeChords, fetchKeys } from '../api/analysis';
import type { AnalysisResponse } from '../types/analysis';
import AnalysisResults from '../components/AnalysisResults';
import WorkbenchLayout from '../components/WorkbenchLayout';
import InputPanel from '../components/InputPanel';
import EmptyAnalysisState from '../components/EmptyAnalysisState';
import CodeModal from '../components/CodeModal';
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
  const [codeModalOpen, setCodeModalOpen] = useState(false);

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

  return (
    <>
      <WorkbenchLayout
        input={
          <InputPanel
            chordsInput={chordsInput}
            onChordsChange={(value) => {
              setChordsInput(value);
              if (error) setError(null);
            }}
            keyOptions={keyOptions}
            selectedKey={selectedKey}
            onKeyChange={setSelectedKey}
            profileOptions={profileOptions}
            selectedProfile={selectedProfile}
            onProfileChange={setSelectedProfile}
            showEducational={showEducational}
            onEducationalChange={setShowEducational}
            loading={loading}
            analyzed={!!results}
            onAnalyze={handleAnalyze}
            showCodeLink={demoMode}
            onViewCode={() => setCodeModalOpen(true)}
          />
        }
        analysis={
          // Two wrappers because the layouts genuinely differ. With results
          // (or an error) we want natural top-to-bottom flow so the right
          // column can scroll. With the empty state we want the whole column
          // height so the dashed card centers vertically per the design spec.
          results || error ? (
            <div className="max-w-3xl mx-auto px-8 py-8 space-y-8">
              {error && (
                <div
                  role="alert"
                  className="rounded-2xl border border-rose-200 bg-rose-50/70 px-5 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
                >
                  <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-rose-700 font-mono mb-1">
                    Error
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 font-serif tracking-tight mb-1.5">
                    Couldn't analyze that
                  </h3>
                  <p className="text-sm text-rose-800">{error}</p>
                </div>
              )}
              {results && (
                <AnalysisResults
                  results={results}
                  showEducational={showEducational}
                  chords={analyzedChords}
                />
              )}
            </div>
          ) : (
            <div className="h-full max-w-3xl mx-auto px-8 py-8 flex flex-col">
              <div className="flex-1 min-h-0">
                <EmptyAnalysisState />
              </div>
            </div>
          )
        }
      />
      <CodeModal
        open={codeModalOpen}
        initialTab="manual"
        initialLang="py"
        onClose={() => setCodeModalOpen(false)}
      />
    </>
  );
};

export default Tab1;
