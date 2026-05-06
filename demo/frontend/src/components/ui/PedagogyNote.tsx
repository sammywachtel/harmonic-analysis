// Inline indigo-tinted callout for short pedagogical asides — the "why does this
// matter to a musician?" voice-over. Quieter than a full SectionCard.

import type { ReactNode } from 'react';

interface PedagogyNoteProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

const PedagogyNote = ({ title = 'Why this matters', children, className = '' }: PedagogyNoteProps) => (
  <div className={`bg-indigo-50/60 border border-indigo-100 rounded-xl px-4 py-3 text-sm text-indigo-900 ${className}`}>
    <div className="flex items-center gap-2 mb-1">
      <svg
        className="w-4 h-4 text-indigo-600"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
      </svg>
      <span className="font-semibold text-indigo-800 text-[10px] uppercase tracking-[0.14em]">
        {title}
      </span>
    </div>
    <div className="leading-relaxed">{children}</div>
  </div>
);

export default PedagogyNote;
