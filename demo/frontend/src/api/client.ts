// Setup play: Axios HTTP client configured for our backend API
// Centralized config means we can swap endpoints easily (dev, staging, prod)

import axios from 'axios';
import { getApiEndpoint } from '../config/environment';

const apiClient = axios.create({
  baseURL: getApiEndpoint(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout - analysis can take a few seconds
});

export default apiClient;
