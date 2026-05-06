// Tab navigation — sub-shell underline pattern from the design README.
// Three tabs (Manual entry · Analyze notation · Audio analysis) sit on a
// hairline separator; the active tab gets a coral underline + slate-900 text.

import { Link, useLocation } from 'react-router-dom';

const TABS = [
  { name: 'Manual entry',     path: '/',       description: 'Type chord symbols and analyze' },
  { name: 'Analyze notation', path: '/upload', description: 'Upload MusicXML or MIDI' },
  { name: 'Audio analysis',   path: '/audio',  description: 'Upload an audio recording' },
];

const TabNavigation = () => {
  const location = useLocation();

  return (
    <div className="border-b border-slate-200 mb-8 -mt-2">
      <nav
        aria-label="Tabs"
        className="max-w-6xl mx-auto flex gap-8 -mb-px"
      >
        {TABS.map((tab) => {
          const isActive = location.pathname === tab.path;
          return (
            <Link
              key={tab.path}
              to={tab.path}
              aria-current={isActive ? 'page' : undefined}
              title={tab.description}
              className={`py-3.5 text-sm transition-colors border-b-2 ${
                isActive
                  ? 'text-slate-900 border-primary-600 font-medium'
                  : 'text-slate-500 hover:text-slate-800 border-transparent'
              }`}
            >
              {tab.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
};

export default TabNavigation;
