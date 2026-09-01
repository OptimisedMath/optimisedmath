'use client';

import type { DeconstructionActions, DeconstructionView } from '@/lib/session';
import DeconstructionIntro from './DeconstructionIntro';
import DeconstructionStep from './DeconstructionStep';
import DeconstructionHandback from './DeconstructionHandback';

interface DeconstructionTakeoverProps {
  view: DeconstructionView;
  actions: DeconstructionActions;
}

/**
 * The opaque full takeover — intro, one step at a time, and the handback
 * screen. Mounted in place of the whole arena (never alongside it), so the
 * original Problem is hidden behind the small header echo each screen carries.
 */
export default function DeconstructionTakeover({ view, actions }: DeconstructionTakeoverProps) {
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950 px-4 py-8">
      <div className="mx-auto flex min-h-full w-full max-w-2xl flex-col items-center justify-center">
        {view.phase === 'intro' && (
          <DeconstructionIntro
            headerQuestion={view.headerQuestion}
            misconceptionName={view.misconceptionName}
            isLoading={view.isLoadingStep && !view.step}
            onBegin={actions.begin}
            onExit={actions.exit}
          />
        )}
        {view.phase === 'step' && view.step && (
          <DeconstructionStep
            headerQuestion={view.headerQuestion}
            step={view.step}
            feedback={view.stepFeedback}
            isSubmitting={view.isSubmittingStep}
            onSubmit={actions.submitStep}
            onExit={actions.exit}
          />
        )}
        {view.phase === 'handback' && view.handbackQuestion && (
          <DeconstructionHandback question={view.handbackQuestion} onReturn={actions.returnToProblem} />
        )}
      </div>
    </div>
  );
}
