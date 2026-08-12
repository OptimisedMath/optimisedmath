import type { Feedback, Problem } from './types';

/**
 * The single post-submit correctness-display rule: which value counts as
 * "correct" to reveal to the student, derived purely from the server-supplied
 * `problem.correct_answer` and `feedback.correct` (ADR-0002 — backend owns
 * game rules; this performs no independent correctness inference).
 *
 * Returns `undefined` when there is nothing to reveal (still awaiting
 * feedback, or the student already answered correctly).
 */
export function getRevealedCorrectAnswer(
  problem: Pick<Problem, 'correct_answer'> | null | undefined,
  feedback: Pick<Feedback, 'correct'> | null | undefined
): string | undefined {
  if (!problem || !feedback || feedback.correct) {
    return undefined;
  }
  return problem.correct_answer;
}
