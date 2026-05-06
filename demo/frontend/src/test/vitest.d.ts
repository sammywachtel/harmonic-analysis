// Type definitions for Vitest + Testing Library matchers.
//
// We extend Vitest's `Assertion` and `AsymmetricMatchersContaining`
// interfaces with the matchers from `@testing-library/jest-dom` so calls like
// `expect(el).toBeInTheDocument()` type-check inside `*.test.tsx`.
//
// `interface ... extends ...` (with no body) is the canonical pattern for
// merging declarations into an existing module — the empty body is the whole
// point. ESLint's `no-empty-object-type` rule flags this as a false positive
// here, so we silence it on these specific lines. Same for the `unknown`
// generic param: TestingLibraryMatchers's first slot is genuinely
// generic-over-anything in this context.

/* eslint-disable @typescript-eslint/no-empty-object-type */
import '@testing-library/jest-dom';
import { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers';

declare module 'vitest' {
  interface Assertion<T = unknown>
    extends TestingLibraryMatchers<typeof expect.stringContaining, T> {}
  interface AsymmetricMatchersContaining
    extends TestingLibraryMatchers<typeof expect.stringContaining, unknown> {}
}
