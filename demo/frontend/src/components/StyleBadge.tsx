// Badge component for displaying musical style with icon and color
// Maps style keys to visual presentation (icons, colors, labels)

import { getStyleConfig } from '../utils/styleConfig';

interface StyleBadgeProps {
  style: string;
  className?: string;
}

const StyleBadge = ({ style, className = '' }: StyleBadgeProps) => {
  const config = getStyleConfig(style);

  return (
    <span
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border ${config.colorClass} ${className}`}
      data-testid={`style-badge-${style.toLowerCase()}`}
    >
      <span className="text-base" aria-hidden="true">
        {config.icon}
      </span>
      <span>{config.label}</span>
    </span>
  );
};

export default StyleBadge;
