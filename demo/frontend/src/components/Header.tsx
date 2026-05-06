// Sticky header per the editorial design spec: white ground, bottom hairline,
// serif wordmark with a small eighth-note glyph, terse nav links on the right.
// Version + "demo" badge tuck into a quiet mono pill next to the wordmark so we
// don't lose the diagnostic context the previous header carried.

import { isDemoMode, getLibraryVersion } from '../config/environment';

const NoteGlyph = () => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className="w-[18px] h-[18px] text-slate-400 flex-shrink-0"
    fill="currentColor"
  >
    {/* Eighth note: stem + flag + filled noteheads. Flat-drawn so it scales clean. */}
    <path d="M19 3v11.55a4 4 0 1 1-2-3.46V6.62L9 8.5v8.55a4 4 0 1 1-2-3.46V6l12-3z" />
  </svg>
);

const Header = () => {
  const demoMode = isDemoMode();
  const version = getLibraryVersion();

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 backdrop-blur supports-[backdrop-filter]:bg-white/85">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 min-w-0">
          <NoteGlyph />
          <span className="font-serif font-semibold text-xl text-slate-900 tracking-tight truncate">
            Harmonic Analysis
          </span>
          <span
            className="hidden sm:inline-flex items-center text-[10px] font-mono uppercase tracking-wider text-slate-500 bg-slate-100 border border-slate-200 rounded-md px-1.5 py-0.5 ml-1"
            title={demoMode ? 'Interactive demo build' : `Library v${version}`}
          >
            v{version}
            {demoMode && ' · demo'}
          </span>
        </div>

        <nav className="flex items-center gap-4 sm:gap-6 text-sm text-slate-600">
          <a
            href="https://github.com/sammywachtel/harmonic-analysis/blob/main/docs/README.md"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-900"
          >
            Docs
          </a>
          <a
            href="https://pypi.org/project/harmonic-analysis/"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:inline hover:text-slate-900"
          >
            API
          </a>
          <a
            href="https://github.com/sammywachtel/harmonic-analysis"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-900"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
};

export default Header;
