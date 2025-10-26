import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Opening move: Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Main play: Clean up after each test to prevent state leakage
afterEach(() => {
  cleanup();
});
