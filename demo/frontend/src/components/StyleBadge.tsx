// Style badge — same data-testid contract as before, restyled to use the Tag
// atom so it visually matches the rest of the chrome.

import Tag from './ui/Tag';
import { getStyleConfig } from '../utils/styleConfig';
import type { TagTone } from './ui/Tag';

interface StyleBadgeProps {
  style: string;
  className?: string;
  'data-testid'?: string;
}

const StyleBadge = ({ style, className = '', ...rest }: StyleBadgeProps) => {
  const config = getStyleConfig(style);
  // Tag's purple/rose/emerald/indigo align with styleConfig tones; fall back
  // to slate for unknown styles.
  const tone = (['indigo', 'purple', 'rose', 'emerald'] as TagTone[]).includes(
    config.tone as TagTone,
  )
    ? (config.tone as TagTone)
    : 'slate';

  // Always emit `style-badge-{style}` so tests can query by style name; the
  // optional override gets emitted as a sibling data attribute (e.g. for
  // marking the "primary" badge in AnalysisResults).
  const stableTestId = `style-badge-${style.toLowerCase()}`;
  const overrideTestId = rest['data-testid'];
  return (
    <span
      data-testid={stableTestId}
      data-role={overrideTestId}
      className={className}
    >
      <Tag tone={tone}>
        <span aria-hidden="true">{config.icon}</span>
        <span>{config.label}</span>
      </Tag>
    </span>
  );
};

export default StyleBadge;
