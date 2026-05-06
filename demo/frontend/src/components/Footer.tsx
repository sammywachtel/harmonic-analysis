// Slim footer — reference links + version, sitting on a hairline divider.
// Keeps the page calm; nothing competes with the Roman numerals up top.

import { getLibraryVersion } from '../config/environment';

const Footer = () => {
  const version = getLibraryVersion();
  const year = new Date().getFullYear();

  return (
    <footer className="mt-12 pt-6 border-t border-slate-200">
      <div className="max-w-6xl mx-auto px-6 pb-8 flex items-center justify-between flex-wrap gap-2 text-xs text-slate-500">
        <div>
          Demo frontend for the{' '}
          <span className="font-mono text-slate-700">harmonic-analysis</span>{' '}
          Python library · v{version} · © {year} MIT License
        </div>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/sammywachtel/harmonic-analysis/blob/main/docs/README.md"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-700"
          >
            API reference
          </a>
          <a
            href="https://github.com/sammywachtel/harmonic-analysis"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-700"
          >
            GitHub
          </a>
          <a
            href="https://github.com/sammywachtel/harmonic-analysis/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-slate-700"
          >
            License
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
