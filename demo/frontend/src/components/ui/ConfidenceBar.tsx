// Horizontal progress bar with optional label and value display.
// Used everywhere we surface a 0..1 confidence: hero card, style breakdown,
// per-chord rows in the audio timeline.

interface ConfidenceBarProps {
  value: number;                 // 0..1, clamped
  color?: 'primary' | 'indigo' | 'amber' | 'rose' | 'emerald' | 'slate';
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showValue?: boolean;
  valueFormat?: (v: number) => string;
  className?: string;
}

const COLORS: Record<NonNullable<ConfidenceBarProps['color']>, string> = {
  primary: 'bg-primary-600',
  indigo:  'bg-indigo-600',
  amber:   'bg-amber-500',
  rose:    'bg-rose-500',
  emerald: 'bg-emerald-500',
  slate:   'bg-slate-400',
};

const ConfidenceBar = ({
  value,
  color = 'primary',
  label,
  size = 'md',
  showValue = true,
  valueFormat,
  className = '',
}: ConfidenceBarProps) => {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const fmt = valueFormat ?? ((v: number) => v.toFixed(2));
  const heightClass = size === 'sm' ? 'h-1.5' : size === 'lg' ? 'h-3' : 'h-2';

  return (
    <div className={`flex items-center gap-2 w-full ${className}`}>
      {label && (
        <span className="text-xs text-slate-600 font-medium min-w-fit">{label}</span>
      )}
      <div className={`flex-1 ${heightClass} bg-slate-100 rounded-full overflow-hidden`}>
        <div
          className={`${heightClass} ${COLORS[color]} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {showValue && (
        <span className="font-mono text-xs tabular-nums text-slate-700 min-w-fit">
          {fmt(value)}
        </span>
      )}
    </div>
  );
};

export default ConfidenceBar;
