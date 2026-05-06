// SectionCard — the universal panel chrome.
// Eyebrow → Title → Subtitle → optional action header, then content body, then
// optional footer slot. Use this everywhere instead of bespoke
// "bg-white border rounded-lg p-6" blocks. Keeps the whole site visually coherent.

import type { ReactNode } from 'react';

interface SectionCardProps {
  eyebrow?: ReactNode;
  title?: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  bodyClassName?: string;
}

const SectionCard = ({
  eyebrow,
  title,
  subtitle,
  action,
  children,
  footer,
  className = '',
  bodyClassName = 'p-6',
}: SectionCardProps) => {
  const hasHeader = title || eyebrow;
  return (
    <section
      className={`bg-white border border-slate-200 rounded-2xl shadow-[0_1px_2px_rgba(15,23,42,0.04)] ${className}`}
    >
      {hasHeader && (
        <header className="px-6 pt-5 pb-4 border-b border-slate-100">
          {eyebrow && (
            <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary-700 mb-1">
              {eyebrow}
            </div>
          )}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="min-w-0 flex-1">
              {title && (
                <h3 className="text-base font-semibold text-slate-900 font-serif tracking-tight">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>
              )}
            </div>
            {action && <div className="shrink-0">{action}</div>}
          </div>
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
      {footer && (
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/60 rounded-b-2xl text-sm text-slate-600">
          {footer}
        </div>
      )}
    </section>
  );
};

export default SectionCard;
