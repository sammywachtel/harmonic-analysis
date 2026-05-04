// Central configuration for musical style metadata
// Maps style keys to visual presentation (icons, colors, labels)

export const STYLE_CONFIG: Record<string, { icon: string; label: string; colorClass: string }> = {
  classical: {
    icon: '🎻',
    label: 'Classical',
    colorClass: 'bg-blue-50 text-blue-700 border-blue-300',
  },
  jazz: {
    icon: '🎷',
    label: 'Jazz',
    colorClass: 'bg-purple-50 text-purple-700 border-purple-300',
  },
  pop: {
    icon: '🎸',
    label: 'Pop/Rock',
    colorClass: 'bg-orange-50 text-orange-700 border-orange-300',
  },
  modal: {
    icon: '🎵',
    label: 'Modal',
    colorClass: 'bg-green-50 text-green-700 border-green-300',
  },
};

// Helper: Get style configuration or fallback
export const getStyleConfig = (style: string) => {
  return STYLE_CONFIG[style.toLowerCase()] || {
    icon: '🎼',
    label: style.charAt(0).toUpperCase() + style.slice(1),
    colorClass: 'bg-slate-50 text-slate-700 border-slate-300',
  };
};
