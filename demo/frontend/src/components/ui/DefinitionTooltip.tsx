// Inline glossary widget. Wraps a phrase with a dotted underline; on hover or
// keyboard focus, a small dark popover shows a definition. Used for
// "how does this work?" affordances next to feature labels.
//
// We expose the popover via both pointer hover AND focus, so keyboard-only
// users can read the definition by tabbing onto the trigger.

import { useState, type ReactNode } from 'react';

interface DefinitionTooltipProps {
  /** What the user reads in-line. Often "how does this work?" or a term. */
  children: ReactNode;
  /** The definition shown in the popover. Plain text or short markup. */
  definition: ReactNode;
  className?: string;
}

const DefinitionTooltip = ({
  children,
  definition,
  className = '',
}: DefinitionTooltipProps) => {
  const [open, setOpen] = useState(false);

  return (
    <span
      className={`relative inline-block border-b border-dotted border-slate-400 cursor-help text-slate-500 ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      tabIndex={0}
      role="button"
      aria-describedby="definition-tooltip-content"
    >
      {children}
      {open && (
        <span
          id="definition-tooltip-content"
          role="tooltip"
          className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-30 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-xl pointer-events-none leading-relaxed font-sans normal-case tracking-normal"
        >
          {definition}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900" />
        </span>
      )}
    </span>
  );
};

export default DefinitionTooltip;
