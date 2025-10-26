// Tab navigation component - switches between Manual Entry and File Upload
// Clean, accessible, and shows which tab is active

import { Link, useLocation } from 'react-router-dom';

const TabNavigation = () => {
  const location = useLocation();

  const tabs = [
    { name: 'Manual Entry', path: '/', description: 'Enter chords manually' },
    { name: 'File Upload', path: '/upload', description: 'Upload music files (coming soon)' },
  ];

  return (
    <div className="border-b border-gray-300 mb-6">
      <nav className="flex space-x-1" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = location.pathname === tab.path;
          return (
            <Link
              key={tab.path}
              to={tab.path}
              className={`
                px-6 py-3 text-sm font-medium rounded-t-lg transition
                ${
                  isActive
                    ? 'bg-white text-blue-700 border-b-2 border-blue-700'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
              title={tab.description}
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
