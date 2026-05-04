// Card displaying per-style analysis details with patterns and features
// Shows confidence, style notes, detected patterns, and characteristic features

import type { StyleAnalysisDetail } from '../types/analysis';
import { getStyleConfig } from '../utils/styleConfig';

interface StyleDetailCardProps {
  styleName: string;
  detail: StyleAnalysisDetail;
  isDominant: boolean;
}

const StyleDetailCard = ({ styleName, detail, isDominant }: StyleDetailCardProps) => {
  const config = getStyleConfig(styleName);

  // Determine card border and background based on style and dominance
  const cardClasses = isDominant
    ? `border-2 ${config.colorClass.split(' ')[1].replace('text-', 'border-')} bg-white`
    : 'border border-slate-300 bg-slate-50';

  return (
    <div
      className={`rounded-lg p-4 ${cardClasses} style-card`}
      data-testid={`style-card-${styleName.toLowerCase()}`}
    >
      {/* Header: icon, title, confidence, dominant badge */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden="true">
            {config.icon}
          </span>
          <h5 className="font-semibold text-slate-900">{config.label} Interpretation</h5>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="px-2 py-1 bg-slate-200 text-slate-800 text-sm font-medium rounded"
            data-testid={`confidence-${styleName.toLowerCase()}`}
          >
            {(detail.confidence * 100).toFixed(0)}%
          </span>
          {isDominant && (
            <span
              className="px-2 py-1 bg-primary-600 text-white text-xs font-semibold rounded"
              data-testid="dominant-badge"
            >
              Primary
            </span>
          )}
        </div>
      </div>

      {/* Style notes: contextual explanation */}
      {detail.style_notes && (
        <p className="text-slate-700 text-sm mb-3 italic" data-testid="style-notes">
          {detail.style_notes}
        </p>
      )}

      {/* Detected patterns */}
      {detail.patterns && detail.patterns.length > 0 && (
        <div className="mb-3">
          <h6 className="text-xs font-semibold text-slate-600 uppercase mb-2">
            Detected Patterns
          </h6>
          <div className="space-y-1">
            {detail.patterns.map((pattern, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-sm"
                data-testid={`pattern-item-${idx}`}
              >
                <span className="text-slate-900">{pattern.name}</span>
                <span className="text-slate-600">{(pattern.score * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Characteristic features */}
      {detail.characteristic_features && detail.characteristic_features.length > 0 && (
        <div>
          <h6 className="text-xs font-semibold text-slate-600 uppercase mb-2">
            Characteristic Features
          </h6>
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
