// Style metadata: each musical style gets one icon + one color family.
// Color families align with the new editorial palette so badges/cards stay
// visually distinct from the coral primary without clashing.

export const STYLE_CONFIG: Record<string, { icon: string; label: string; colorClass: string; tone: 'indigo' | 'purple' | 'rose' | 'emerald' | 'slate' }> = {
  classical: {
    icon: '🎻',
    label: 'Classical',
    colorClass: 'bg-indigo-50 text-indigo-800 border-indigo-200',
    tone: 'indigo',
  },
  jazz: {
    icon: '🎷',
    label: 'Jazz',
    colorClass: 'bg-purple-50 text-purple-800 border-purple-200',
    tone: 'purple',
  },
  pop: {
    icon: '🎸',
    label: 'Pop/Rock',
    colorClass: 'bg-rose-50 text-rose-800 border-rose-200',
    tone: 'rose',
  },
  modal: {
    icon: '🎵',
    label: 'Modal',
    colorClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    tone: 'emerald',
  },
};

// Helper: return the config for a known style or a sensible slate fallback.
export const getStyleConfig = (style: string) => {
  return STYLE_CONFIG[style.toLowerCase()] || {
    icon: '🎼',
    label: style.charAt(0).toUpperCase() + style.slice(1),
    colorClass: 'bg-slate-50 text-slate-700 border-slate-200',
    tone: 'slate' as const,
  };
};
