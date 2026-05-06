// Tiny uppercase label — the editorial "eyebrow" that introduces a section
// without competing with the headline. Tracking and weight are tuned for the
// design's score-inspired layout.

import type { ReactNode } from 'react';

interface EyebrowProps {
  children: ReactNode;
  tone?: 'primary' | 'slate' | 'indigo';
  className?: string;
}

const TONES: Record<NonNullable<EyebrowProps['tone']>, string> = {
  primary: 'text-primary-700',
  slate:   'text-slate-500',
  indigo:  'text-indigo-700',
};

const Eyebrow = ({ children, tone = 'slate', className = '' }: EyebrowProps) => (
  <div
    className={`text-[10px] font-semibold uppercase tracking-[0.14em] font-mono ${TONES[tone]} ${className}`}
  >
    {children}
  </div>
);

export default Eyebrow;
