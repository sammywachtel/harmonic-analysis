// Two-column "workbench" frame used by Tab 1. The whole point is that the
// input column never moves while the analysis column scrolls independently —
// the user can keep editing chords without losing sight of where they are.
//
// Height math (matters because we escape Layout's chrome to claim viewport):
//   - Header is sticky h-14 = 56px.
//   - Layout's <main> has px-6 py-8 (24px sides, 32px top/bottom).
//   - TabNavigation sits inside main with -mt-2 mb-8, contributing about
//     46px of content + 32px bottom gap.
//   - We escape with `-mt-8 -mx-6` (cancels main's pt-8 and the tabnav gap +
//     pulls flush to the edges), then claim `h-[calc(100vh-7.5rem)]` — that
//     leaves room for the header, tabnav, and a hair of breathing space.
//
// Footer continues to live inside Layout but ends up below the viewport on
// this tab. The user can scroll the page to reveal it; the workbench area
// itself doesn't scroll — only the right column does. That's the design
// intent: a fixed working surface with a scrolling result feed.

import type { ReactNode } from 'react';

interface WorkbenchLayoutProps {
  input: ReactNode;
  analysis: ReactNode;
}

const WorkbenchLayout = ({ input, analysis }: WorkbenchLayoutProps) => (
  <div className="-mt-8 -mx-6 h-[calc(100vh-7.5rem)] flex border-t border-slate-200 bg-white overflow-hidden">
    <aside className="w-[340px] flex-shrink-0 h-full bg-white border-r border-slate-200 flex flex-col overflow-hidden">
      {input}
    </aside>
    <section className="flex-1 min-w-0 h-full overflow-y-auto bg-slate-50">
      {analysis}
    </section>
  </div>
);

export default WorkbenchLayout;
