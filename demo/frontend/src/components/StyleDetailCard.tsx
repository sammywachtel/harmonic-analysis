// Per-style breakdown card — restyled to match the SectionCard family while
// preserving all the data-testid hooks the e2e suite relies on.

import type { StyleAnalysisDetail } from '../types/analysis';
import { getStyleConfig } from '../utils/styleConfig';
import Tag from './ui/Tag';
import type { TagTone } from './ui/Tag';

interface StyleDetailCardProps {
  styleName: string;
  detail: StyleAnalysisDetail;
  isDominant: boolean;
}

const StyleDetailCard = ({ styleName, detail, isDominant }: StyleDetailCardProps) => {
  const config = getStyleConfig(styleName);
  const tone = (['indigo', 'purple', 'rose', 'emerald'] as TagTone[]).includes(
    config.tone as TagTone,
  )
    ? (config.tone as TagTone)
    : 'slate';

  // Dominant style gets a coral primary border; the rest get the quiet slate.
  const containerClasses = isDominant
    ? 'border-2 border-primary-300 bg-white shadow-[0_2px_8px_rgba(15,23,42,0.06)]'
    : 'border border-slate-200 bg-slate-50/40';

  return (
    <div
      className={`rounded-xl p-4 ${containerClasses} style-card`}
      data-testid={`style-card-${styleName.toLowerCase()}`}
    >
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden="true">{config.icon}</span>
          <h5 className="font-serif font-semibold text-slate-900 tracking-tight">
            {config.label} interpretation
          </h5>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="px-2 py-0.5 bg-slate-100 text-slate-800 text-xs font-mono tabular-nums rounded-md border border-slate-200"
            data-testid={`confidence-${styleName.toLowerCase()}`}
          >
            {(detail.confidence * 100).toFixed(0)}%
          </span>
          {isDominant && (
            <span data-testid="dominant-badge">
              <Tag tone="primary">Primary</Tag>
            </span>
          )}
          {!isDominant && <Tag tone={tone}>{config.label}</Tag>}
        </div>
      </div>

      {detail.style_notes && (
        <p
          className="text-sm text-slate-600 italic leading-relaxed mb-3"
          data-testid="style-notes"
        >
          {detail.style_notes}
        </p>
      )}

      {detail.patterns && detail.patterns.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500 mb-2">
            Detected patterns
          </div>
          <div className="space-y-1">
            {detail.patterns.map((pattern, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-sm"
                data-testid={`pattern-item-${idx}`}
              >
                <span className="text-slate-900">{pattern.name}</span>
                <span className="text-slate-500 font-mono tabular-nums text-xs">
                  {(pattern.score * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {detail.characteristic_features && detail.characteristic_features.length > 0 && (
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500 mb-2">
            Characteristic features
          </div>
          <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
            {detail.characteristic_features.map((feature, idx) => (
              <li key={idx} data-testid={`feature-${idx}`}>
                {feature}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default StyleDetailCard;
