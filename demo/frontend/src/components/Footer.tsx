// Footer component - version info, links, copyright
// Keep it simple and informative

import { getLibraryVersion } from '../config/environment';

const Footer = () => {
  const version = getLibraryVersion();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-100 border-t border-gray-300 mt-auto">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-sm text-gray-600">
            <p>Harmonic Analysis Library v{version}</p>
            <p className="text-xs mt-1">© {currentYear} MIT License</p>
          </div>

          <div className="flex space-x-6 text-sm">
            <a
              href="https://github.com/sammywachtel/harmonic-analysis"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 transition"
            >
              GitHub
            </a>
            <a
              href="https://github.com/sammywachtel/harmonic-analysis/blob/main/docs/README.md"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 transition"
            >
              Documentation
            </a>
            <a
              href="https://github.com/sammywachtel/harmonic-analysis/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 transition"
            >
              License
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
