import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { useSession, type FeedbackPhase } from '@/lib/session';
import { resetFakeBackend, mockApi } from './apiMock';
import { baseProblem, baseSession, wireArenaFlow } from './fakeBackend';
import { resetStoredSession, seedStoredSession } from './testSession';

async function waitForPhase(
  getPhase: () => FeedbackPhase,
  expected: FeedbackPhase
) {
  await waitFor(() => {
    expect(getPhase()).toBe(expected);
  });
}

async function waitForSessionReady() {
  await waitFor(() => {
    expect(mockApi.post).toHaveBeenCalledWith('/session/start', expect.anything());
    expect(mockApi.get).toHaveBeenCalledWith('/problem/next', expect.anything());
  });
}

describe('feedbackPhase on SessionView', () => {
  beforeEach(() => {
    resetFakeBackend();
    resetStoredSession();
    seedStoredSession();
  });

  it('is none when the session payload has no feedback', async () => {
    const session = baseSession({ feedback_type: null, feedback_msg: '' });
    const problem = baseProblem();

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({ is_correct: true, feedback: '', state: session }),
    });

    const { result } = renderHook(() => useSession());
    await waitForSessionReady();
    await waitForPhase(() => result.current.view.feedbackPhase, 'none');
  });

  it('is soft_error when feedback is present and can_next_problem is false', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: false,
        feedback: 'Zły format odpowiedzi',
        state: {
          ...session,
          problem_answered: false,
          can_submit: true,
          can_next_problem: false,
          feedback_type: 'info',
          feedback_msg: 'Zły format odpowiedzi',
          current_problem: problem,
        },
      }),
    });

    const { result } = renderHook(() => useSession());
    await waitForSessionReady();
    await result.current.actions.submit('4/');
    await waitForPhase(() => result.current.view.feedbackPhase, 'soft_error');
  });

  it('is answer_locked when correct feedback has can_next_problem true', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: true,
        feedback: 'Brawo!',
        state: {
          ...session,
          problem_answered: true,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'success',
          feedback_msg: 'Brawo!',
          current_problem: problem,
        },
      }),
    });

    const { result } = renderHook(() => useSession());
    await waitForSessionReady();
    await result.current.actions.submit('4');
    await waitForPhase(() => result.current.view.feedbackPhase, 'answer_locked');
  });

  it('is answer_locked when wrong feedback has can_next_problem true', async () => {
    const session = baseSession();
    const problem = baseProblem();

    wireArenaFlow({
      session,
      problem,
      onSubmit: () => ({
        is_correct: false,
        feedback: 'Wrong feedback',
        state: {
          ...session,
          problem_answered: true,
          can_submit: false,
          can_next_problem: true,
          feedback_type: 'warning',
          feedback_msg: 'Wrong feedback',
          current_problem: problem,
        },
      }),
    });

    const { result } = renderHook(() => useSession());
    await waitForSessionReady();
    await result.current.actions.submit('3');
    await waitForPhase(() => result.current.view.feedbackPhase, 'answer_locked');
  });
});
