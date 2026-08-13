import { type RefObject } from 'react';
import FeedbackCard from './FeedbackCard';
import type { SessionActions, SessionView } from '@/lib/session';

interface FeedbackPresenterProps {
  view: SessionView;
  actions: SessionActions;
  feedbackRef?: RefObject<HTMLDivElement | null>;
  nextButtonRef?: RefObject<HTMLButtonElement | null>;
}

export default function FeedbackPresenter({
  view,
  actions,
  feedbackRef,
  nextButtonRef,
}: FeedbackPresenterProps) {
  const { feedbackPhase, feedback } = view;

  if (feedbackPhase === 'none' || !feedback) {
    return null;
  }

  if (feedbackPhase === 'soft_error') {
    return (
      <div
        ref={feedbackRef}
        data-feedback-type={feedback.feedback_type ?? ''}
        className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-700 text-base sm:text-lg font-semibold text-center dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300"
      >
        {feedback.message}
      </div>
    );
  }

  return (
    <FeedbackCard
      view={view}
      actions={actions}
      nextButtonRef={nextButtonRef}
    />
  );
}
