// Inline pill / status tag. Single source of truth for "small colored chip".
// Eight tones map to the design palette; pick the one whose meaning matches.

import type { ReactNode } from 'react';

export type TagTone =
  | 'slate'
  | 'primary'
  | 'indigo'
  | 'amber'
  | 'rose'
  | 'emerald'
  | 'purple'
  | 'orange';

interface TagProps {
  tone?: TagTone;
  children: ReactNode;
  className?: string;
  title?: string;
}

const TONES: Record<TagTone, string> = {
  slate:   'bg-slate-100 text-slate-700 border-slate-200',
  primary: 'bg-primary-50 text-primary-800 border-primary-200',
  indigo:  'bg-indigo-50 text-indigo-800 border-indigo-200',
  amber:   'bg-amber-50 text-amber-800 border-amber-200',
  rose:    'bg-rose-50 text-rose-800 border-rose-200',
  emerald: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  purple:  'bg-purple-50 text-purple-800 border-purple-200',
  orange:  'bg-orange-50 text-orange-800 border-orange-200',
};

const Tag = ({ tone = 'slate', children, className = '', title }: TagProps) => (
  <span
    title={title}
    className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium border rounded-full ${TONES[tone]} ${className}`}
  >
    {children}
  </span>
);

export default Tag;
