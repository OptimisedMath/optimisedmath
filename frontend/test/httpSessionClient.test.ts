import { beforeEach, describe, expect, it, vi } from 'vitest';
import { baseProblem, baseSession } from './fakeBackend';
import type { ProblemResponse, SubmissionResponse } from '@/lib/session/types';

const { mockPost, mockGet } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockGet: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  default: { post: mockPost, get: mockGet },
}));

const { httpSessionClient } = await import('@/lib/session/httpSessionClient');

describe('httpSessionClient', () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGet.mockReset();
  });

  it('maps a served Problem returned by getNextProblem', async () => {
    const problem = baseProblem();
    const payload: ProblemResponse = { problem, state: baseSession() };
    mockGet.mockResolvedValue({ data: payload });

    const response = await httpSessionClient.getNextProblem('sess-test');

    expect(mockGet).toHaveBeenCalledWith('/problem/next', { params: { session_id: 'sess-test' } });
    expect(response).toEqual(payload);
  });

  it('maps a graded Submission returned by submitAnswer', async () => {
    const payload: SubmissionResponse = {
      is_correct: true,
      feedback: 'Brawo!',
      state: baseSession({ feedback_type: 'success', feedback_msg: 'Brawo!' }),
    };
    mockPost.mockResolvedValue({ data: payload });

    const request = { session_id: 'sess-test', problem_id: 'prob-1', user_input: '4' };
    const response = await httpSessionClient.submitAnswer(request);

    expect(mockPost).toHaveBeenCalledWith('/problem/submit', request);
    expect(response).toEqual(payload);
  });

  it('maps a Navigation returned by navigateSession', async () => {
    const nextState = baseSession({ selected_topic_id: 2 });
    mockPost.mockResolvedValue({ data: nextState });

    const request = { session_id: 'sess-test', selected_topic_id: 2 };
    const response = await httpSessionClient.navigateSession(request);

    expect(mockPost).toHaveBeenCalledWith('/session/navigate', request);
    expect(response).toEqual(nextState);
  });

  it('propagates a rejected request as an error', async () => {
    mockPost.mockRejectedValue(new Error('Network error'));

    await expect(
      httpSessionClient.startSession({ username: 'testuser' })
    ).rejects.toThrow('Network error');
  });
});
