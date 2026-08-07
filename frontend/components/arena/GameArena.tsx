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
  const {
    sessionState,
    feedback,
    error,
    isNavigating,
    isAdvancing,
    needsLogin,
    problem,
    handleSubmit,
    handleAutoSolve,
    handleNavigate,
    handleAdvance,
    handleReset,
    clearErrorAndReload,
    showAdvance,
    canSubmit,
    adminMode,
    radioOnly,
  } = useSession();

  const feedbackRef = useRef<HTMLDivElement>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!feedback) return;

    const frameId = requestAnimationFrame(() => {
      const target = feedback.is_locked ? nextButtonRef.current : feedbackRef.current;
      if (target) {
        scrollElementClearOfMobileChrome(target);
      }
    });

    return () => cancelAnimationFrame(frameId);
  }, [feedback]);

  if (error) {
    return (
      <div className="gradient-bg flex h-screen items-center justify-center p-8 text-slate-900 dark:text-white">
        <div className="glass-card-strong animate-scale-in max-w-md rounded-2xl p-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-3xl dark:bg-red-400/15">
            ⚠️
          </div>
          <h2 className="text-2xl font-bold mb-4 text-red-600 dark:text-red-300">Wystąpił błąd</h2>
          <p className="text-lg mb-6 text-slate-600 dark:text-slate-300">{error}</p>
          <button
            onClick={clearErrorAndReload}
            className="bg-red-600 hover:bg-red-500 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] text-white px-6 py-2 rounded-lg font-bold transition-all shadow-lg shadow-red-500/30"
          >
            Spróbuj ponownie
          </button>
        </div>
      </div>
    );
  }

  if (!sessionState) {
    return (
      <div className="gradient-bg flex h-screen flex-col items-center justify-center gap-4 text-slate-900 dark:text-white">
        <Spinner className="h-8 w-8 text-sky-500 dark:text-sky-400" />
        <span className="text-lg font-semibold text-slate-600 dark:text-slate-300">
          {needsLogin ? 'Przekierowywanie do logowania...' : 'Łączenie z serwerem...'}
        </span>
      </div>
    );
  }

  return (
    <div className="gradient-bg relative min-h-screen overflow-hidden p-3 pb-6 text-slate-900 sm:p-6 lg:p-8 dark:text-white font-sans flex flex-col items-center">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 border-b border-white/50 bg-white/30 backdrop-blur-3xl dark:border-white/5 dark:bg-white/5" />
      <div className="relative z-10 flex w-full flex-col items-center">
      <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '0ms' }}>
      <XPBar
        xp={sessionState.xp}
        flawlessEligible={sessionState.flawless_eligible}
      />
      </div>

      {sessionState.navigation && (
        <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '80ms' }}>
          <TopicToolbar
            sessionState={sessionState}
            isNavigating={isNavigating}
            onNavigate={handleNavigate}
            onReset={handleReset}
          />
        </div>
      )}

      {sessionState.navigation && (
        <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '160ms' }}>
          <ProgressBar
            type="chapter"
            selectedChapterName={
              sessionState.navigation.available_chapters.find(
                (chapter) => chapter.chapter_id === sessionState.selected_chapter_id
              )?.name
            }
            chapterProgress={sessionState.navigation.chapter_progress}
          />
          <ProgressBar
            type="topic"
            selectedLevel={sessionState.selected_level}
            topicProgress={sessionState.navigation.topic_progress}
            currentTopicName={sessionState.navigation.current_topic_name}
          />
        </div>
      )}

      <div className="animate-fade-slide-up w-full flex flex-col items-center" style={{ animationDelay: '240ms' }}>
        <MasteryScoreboard
          streak={sessionState.streak}
          maxStreak={sessionState.max_streak}
          problemAnswered={sessionState.problem_answered}
          levelCompleted={sessionState.level_completed}
        />
      </div>

      <div
        className="glass-card-strong animate-fade-slide-up relative w-full max-w-3xl overflow-hidden rounded-2xl p-4 text-center sm:p-8"
        style={{ animationDelay: '320ms' }}
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-sky-400 via-emerald-400 to-amber-300" />
        <ProblemDisplay
          problem={problem}
          selectedChapterName={
            sessionState.navigation?.available_chapters.find(
              (chapter) => chapter.chapter_id === sessionState.selected_chapter_id
            )?.name ?? null
          }
          selectedLevel={sessionState.selected_level}
          topicName={sessionState.navigation?.current_topic_name ?? 'Aktualny temat'}
          isLoading={!problem}
        />

        {problem && (
          <>
            <AnswerInput
              key={problem.problem_id}
              onSubmit={handleSubmit}
              disabled={!canSubmit}
              canSubmit={canSubmit}
              showFeedback={showAdvance}
              problem={problem}
              currentInputMode={sessionState.current_input_mode}
              feedback={feedback}
              radioOnly={radioOnly}
              onAutoSolve={adminMode ? handleAutoSolve : undefined}
            />

            {feedback && !showAdvance && (
              <div
                ref={feedbackRef}
                className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-700 text-base sm:text-lg font-semibold text-center dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300"
              >
                {feedback.message}
              </div>
            )}

            {feedback && showAdvance && (
              <FeedbackCard
                feedback={feedback}
                onNextProblem={handleAdvance}
                topicCompleted={sessionState.topic_completed}
                levelCompleted={sessionState.level_completed}
                hasNextTopic={sessionState.navigation?.has_next_unlocked_topic ?? false}
                currentInputMode={sessionState.current_input_mode}
                disabled={isAdvancing}
                nextButtonRef={nextButtonRef}
                problem={problem}
              />
            )}
          </>
        )}
      </div>
      </div>
    </div>
  );
}
