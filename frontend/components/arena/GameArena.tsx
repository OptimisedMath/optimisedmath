'use client';

import { useEffect, useRef } from 'react';
import { useSession } from '@/lib/session';
import { scrollElementClearOfMobileChrome } from '@/lib/scroll';
import { Spinner } from '@/components/ui/spinner';
import XPBar from './XPBar';
import TopicToolbar from './TopicToolbar';
import ProblemDisplay from './ProblemDisplay';
import AnswerInput from './AnswerInput';
import FeedbackCard from './FeedbackCard';
import ProgressBar from './ProgressBar';
import MasteryScoreboard from './MasteryScoreboard';

export default function GameArena() {
  const { view, actions } = useSession();

  const feedbackRef = useRef<HTMLDivElement>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!view.feedback) return;

    const frameId = requestAnimationFrame(() => {
      const target = view.feedback!.answer_locked ? nextButtonRef.current : feedbackRef.current;
      if (target) {
        scrollElementClearOfMobileChrome(target);
      }
    });

    return () => cancelAnimationFrame(frameId);
  }, [view.feedback]);

  if (view.error) {
    return (
      <div className="gradient-bg flex h-screen items-center justify-center p-8 text-slate-900 dark:text-white">
        <div className="glass-card-strong animate-scale-in max-w-md rounded-2xl p-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-3xl dark:bg-red-400/15">
            ⚠️
          </div>
          <h2 className="text-2xl font-bold mb-4 text-red-600 dark:text-red-300">Wystąpił błąd</h2>
          <p className="text-lg mb-6 text-slate-600 dark:text-slate-300">{view.error}</p>
          <button
            onClick={actions.clearErrorAndReload}
            className="bg-red-600 hover:bg-red-500 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] text-white px-6 py-2 rounded-lg font-bold transition-all shadow-lg shadow-red-500/30"
          >
            Spróbuj ponownie
          </button>
        </div>
      </div>
    );
  }

  if (view.isLoading) {
    return (
      <div className="gradient-bg flex h-screen flex-col items-center justify-center gap-4 text-slate-900 dark:text-white">
        <Spinner className="h-8 w-8 text-sky-500 dark:text-sky-400" />
        <span className="text-lg font-semibold text-slate-600 dark:text-slate-300">
          {view.needsLogin ? 'Przekierowywanie do logowania...' : 'Łączenie z serwerem...'}
        </span>
      </div>
    );
  }

  return (
    <div className="gradient-bg relative min-h-screen overflow-hidden p-3 pb-6 text-slate-900 sm:p-6 lg:p-8 dark:text-white font-sans flex flex-col items-center">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 border-b border-white/50 bg-white/30 backdrop-blur-3xl dark:border-white/5 dark:bg-white/5" />
      <div className="relative z-10 flex w-full flex-col items-center">
      <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '0ms' }}>
      <XPBar view={view} />
      </div>

      {view.hasNavigation && (
        <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '80ms' }}>
          <TopicToolbar view={view} actions={actions} />
        </div>
      )}

      {view.hasNavigation && (
        <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '160ms' }}>
          <ProgressBar type="chapter" view={view} />
          <ProgressBar type="topic" view={view} />
        </div>
      )}

      <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '240ms' }}>
        <MasteryScoreboard view={view} />
      </div>

      <div
        className="glass-card-strong animate-fade-slide-up relative w-full max-w-3xl overflow-hidden rounded-2xl p-4 text-center sm:p-8"
        style={{ animationDelay: '320ms' }}
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-sky-400 via-emerald-400 to-amber-300" />
        <ProblemDisplay view={view} />

        {view.problem && (
          <>
            <AnswerInput key={view.problem.problem_id} view={view} actions={actions} />

            {view.feedback && !view.canNextProblem && (
              <div
                ref={feedbackRef}
                data-feedback-type={view.feedback.feedback_type ?? ''}
                className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-700 text-base sm:text-lg font-semibold text-center dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300"
              >
                {view.feedback.message}
              </div>
            )}

            {view.feedback && view.canNextProblem && (
              <FeedbackCard
                view={view}
                actions={actions}
                nextButtonRef={nextButtonRef}
              />
            )}
          </>
        )}
      </div>
      </div>
    </div>
  );
}
