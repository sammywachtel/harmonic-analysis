// Placeholder shown in the right column of the workbench before the user has
// run an analysis. The outer wrapper claims `h-full` so the dashed card can
// stretch and center against the available column height — without this the
// card would float near the top of a tall right column, looking lonely.

import Eyebrow from './ui/Eyebrow';

const EmptyAnalysisState = () => (
  <div className="h-full min-h-[24rem] rounded-2xl border border-dashed border-slate-300 bg-white/50 flex flex-col items-center justify-center text-center px-8 py-12">
    <Eyebrow className="mb-2">Waiting for input</Eyebrow>
    <h2 className="font-serif text-2xl text-slate-900 mb-2 tracking-tight">
      No analysis yet
    </h2>
    <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
      Edit the chords on the left and press{' '}
      <span className="font-mono text-slate-700">Analyze</span> to see the engine's reading here.
    </p>
  </div>
);

export default EmptyAnalysisState;
