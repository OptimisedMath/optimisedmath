import { describe, expect, it } from 'vitest';
import { baseSession, createFakeSessionClient } from './fakeBackend';

describe('createFakeSessionClient (in-memory adapter)', () => {
  it('rejects an unwired operation instead of silently succeeding', async () => {
    const client = createFakeSessionClient();

    await expect(client.startSession({ username: 'testuser' })).rejects.toThrow(
      'Unhandled startSession'
    );
  });

  it('produces an error response for a wired operation', async () => {
    const client = createFakeSessionClient({
      startSession: async () => {
        throw new Error('Session expired');
      },
    });

    await expect(client.startSession({ username: 'testuser' })).rejects.toThrow(
      'Session expired'
    );
  });

  it('produces a soft-error Submission — feedback present, next problem still locked out', async () => {
    const client = createFakeSessionClient({
      submitAnswer: async () => ({
        is_correct: false,
        feedback: 'Zły format odpowiedzi',
        state: baseSession({
          can_submit: true,
          can_next_problem: false,
          feedback_type: 'info',
          feedback_msg: 'Zły format odpowiedzi',
        }),
      }),
    });

    const response = await client.submitAnswer({
      session_id: 'sess-test',
      problem_id: 'prob-1',
      user_input: '4/',
    });

    expect(response.is_correct).toBe(false);
    expect(response.state.feedback_type).toBe('info');
    expect(response.state.can_next_problem).toBe(false);
  });

  it('records the domain-shaped request each spy received', async () => {
    const client = createFakeSessionClient({
      submitAnswer: async () => ({ is_correct: true, feedback: '', state: baseSession() }),
    });

    const request = { session_id: 'sess-test', problem_id: 'prob-1', user_input: '4' };
    await client.submitAnswer(request);

    expect(client.submitAnswer).toHaveBeenCalledWith(request);
  });
});
