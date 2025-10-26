// Environment configuration - detects demo vs production mode
// Demo mode shows Python code examples, production mode is more user-friendly

export const isDemoMode = (): boolean => {
  return import.meta.env.VITE_DEMO_MODE === 'true';
};

export const getApiEndpoint = (): string => {
  return import.meta.env.VITE_API_ENDPOINT || 'http://localhost:8000';
};

export const getLibraryVersion = (): string => {
  // This will match the version in the backend API
  return '1.0.0';
};
