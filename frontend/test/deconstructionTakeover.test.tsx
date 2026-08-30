import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Problem, SessionClient, SessionResponse } from '@/lib/session';
import {
  baseDeconstructionStep,
  baseProblem,
  baseSession,
  createFakeSessionClient,
  withoutCorrectAnswer,
  withProblem,
} from './fakeBackend';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

async function waitForArenaReady(client: SessionClient) {
  await waitFor(() => {
    expect(client.startSession).toHaveBeenCalled();
    expect(client.getNextProblem).toHaveBeenCalled();
  });
  await waitFor(() => {
    expect(screen.queryByText('Ładowanie zadania...')).not.toBeInTheDocument();
  });
}

async function submitTypedAnswer(answer: string) {
  const user = userEvent.setup();
  const input = await screen.findByPlaceholderText('Wpisz wynik...');
  await user.clear(input);
  await user.type(input, answer);
  await user.click(screen.getByRole('button', { name: /Sprawdź odpowiedź/ }));
}

function triggeringState(session: SessionResponse, triggerProblem: Problem): SessionResponse {
  const locked = {
    ...session,
    can_submit: false,
    can_next_problem: true,
    feedback_type: 'warning',
    feedback_msg: 'Trap feedback',
  };
  return withProblem(locked, triggerProblem);
}

/** Wires a full arena flow up through a triggering (Deconstruction-arming) Submission. */
function wireTriggeringFlow({
  session,
  initialProblem,
  triggerProblem,
  step,
  ...handlers
}: {
  session: SessionResponse;
  initialProblem: Problem;
  triggerProblem: Problem;
  step: ReturnType<typeof baseDeconstructionStep>;
} & Partial<SessionClient>): SessionClient {
  return createFakeSessionClient({
    startSession: async () => session,
    getNextProblem: async () => ({
      problem: initialProblem,
      state: {
        ...withProblem(session, initialProblem),
        can_submit: true,
        can_next_problem: false,
      },
    }),
    submitAnswer: async () => ({
      is_correct: false,
      feedback: 'Trap feedback',
      state: triggeringState(session, triggerProblem),
    }),
    getDeconstructionStep: async () => step,
    ...handlers,
  });
}

/** Drives the arena from a fresh session through a triggering Submission into the pause. */
async function reachPause(client: SessionClient) {
  renderArena(client);
  await waitForArenaReady(client);
  await submitTypedAnswer('3/4');
  await screen.findByText('Trap feedback');
}

/** Drives the arena all the way to the 'step' phase (taps through pause and intro). */
async function reachStep(client: SessionClient, step: ReturnType<typeof baseDeconstructionStep>) {
  await reachPause(client);

  const user = userEvent.setup();
  await user.click(screen.getByLabelText('Przejdź dalej'));
  await screen.findByText(step.misconception_name);
  await user.click(screen.getByRole('button', { name: /Zaczynajmy/ }));
  await screen.findByText(`krok ${step.step_index + 1} z ${step.total_steps}`);
}

describe('Deconstruction takeover', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('holds the Trap prose on screen during the pause and taps through to the takeover', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep();

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    await reachPause(client);
    expect(screen.getByLabelText('Przejdź dalej')).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByLabelText('Przejdź dalej'));

    await screen.findByText('Zatrzymajmy się na chwilę');
    expect(screen.queryByText('Trap feedback')).not.toBeInTheDocument();
  });

  it('auto-advances from the pause to the takeover after 4 seconds without a tap', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep();

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    renderArena(client);
    await waitForArenaReady(client);

    const user = userEvent.setup();
    const input = await screen.findByPlaceholderText('Wpisz wynik...');
    await user.clear(input);
    await user.type(input, '3/4');

    // The pause's setTimeout must be created while fake timers are already
    // installed, so timers switch over before the Submission that arms it.
    vi.useFakeTimers();
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Sprawdź odpowiedź/ }));
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4000);
    });

    expect(screen.getByText('Zatrzymajmy się na chwilę')).toBeInTheDocument();
  });

  it('names the Misconception on the intro screen and disclaims points and streak', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep({ misconception_name: 'Dodawanie ułamków wprost' });

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    await reachPause(client);
    await userEvent.setup().click(screen.getByLabelText('Przejdź dalej'));

    await screen.findByText('Dodawanie ułamków wprost');
    expect(screen.getByText(/nie stracisz za to punktów ani serii/i)).toBeInTheDocument();
  });

  it('hides the original Problem behind a small header echo during the walkthrough', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep();

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    await reachStep(client, step);

    // The full Problem display (heading, input, submit row) is gone entirely —
    // not just visually covered — while only a small echo remains.
    expect(screen.queryByText('Zadanie')).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Wpisz wynik...')).not.toBeInTheDocument();
    const echo = document.querySelector('[data-deconstruction-question]');
    expect(echo).not.toBeNull();
  });

  it('renders exactly one step with progress dots and a working line that updates in place', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep({
      step_index: 0,
      total_steps: 3,
      working_line: '\\frac{2}{3}+\\frac{1}{4}',
    });

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    await reachStep(client, step);

    expect(screen.getByText('krok 1 z 3')).toBeInTheDocument();
    expect(document.querySelectorAll('[data-deconstruction-dot]').length).toBe(3);
    expect(document.querySelector('[data-deconstruction-working-line]')).not.toBeNull();
  });

  it('renders a step without a working line rather than padding it with an empty device', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep({ working_line: null });

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    await reachStep(client, step);

    expect(document.querySelector('[data-deconstruction-working-line]')).toBeNull();
  });

  it('renders the Reveal in place and still requires the Student to type the answer', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep({ revealed_answer: '5/12' });

    const submitDeconstructionStep = vi.fn(async () => ({
      is_correct: true,
      feedback_msg: null,
      handback_question: null,
    }));

    const client = wireTriggeringFlow({
      session,
      initialProblem,
      triggerProblem,
      step,
      submitDeconstructionStep,
      getDeconstructionStep: vi.fn(async () => step),
    });

    await reachStep(client, step);

    expect(screen.getByText('5/12')).toBeInTheDocument();
    const input = screen.getByPlaceholderText('?');
    expect(input).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(input, '5/12');
    await user.click(screen.getByRole('button', { name: 'Sprawdź' }));

    await waitFor(() => {
      expect(submitDeconstructionStep).toHaveBeenCalledWith({
        session_id: session.session_id,
        user_input: '5/12',
      });
    });
  });

  it('keeps the exit control present on every step and visually recessive', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep();

    const client = wireTriggeringFlow({ session, initialProblem, triggerProblem, step });

    await reachStep(client, step);

    const exitControl = screen.getByRole('button', { name: /Zrezygnuj/ });
    expect(exitControl).toBeInTheDocument();
    expect(exitControl.className).toContain('opacity-60');
  });

  it('abandoning via the exit control returns to the arena with the Problem locked and revealed', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const step = baseDeconstructionStep();

    const revealedTriggerProblem = { ...triggerProblem, correct_answer: '4' };
    const abandonDeconstruction = vi.fn(async () => {
      const locked = {
        ...session,
        can_submit: false,
        can_next_problem: true,
        feedback_type: 'warning',
        feedback_msg: 'Trap feedback',
      };
      return withProblem(locked, revealedTriggerProblem);
    });

    const client = wireTriggeringFlow({
      session,
      initialProblem,
      triggerProblem,
      step,
      abandonDeconstruction,
    });

    await reachStep(client, step);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Zrezygnuj/ }));

    await waitFor(() => {
      expect(abandonDeconstruction).toHaveBeenCalledWith({ session_id: session.session_id });
    });

    await screen.findByText('Trap feedback');
    expect(screen.queryByText('Rozkładamy zadanie')).not.toBeInTheDocument();
    expect(screen.getByText('Poprawna odpowiedź:')).toBeInTheDocument();
  });

  it('restates the Problem on the handback screen and re-enables the same Problem on return', async () => {
    const session = baseSession();
    const initialProblem = baseProblem();
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const finalStep = baseDeconstructionStep({ step_index: 1, total_steps: 2 });

    const submitDeconstructionStep = vi.fn(async () => ({
      is_correct: true,
      feedback_msg: null,
      handback_question: triggerProblem.question,
    }));

    const client = wireTriggeringFlow({
      session,
      initialProblem,
      triggerProblem,
      step: finalStep,
      submitDeconstructionStep,
    });

    await reachStep(client, finalStep);

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText('?'), '5/12');
    await user.click(screen.getByRole('button', { name: 'Sprawdź' }));

    await screen.findByText('Rozłożone na kroki');
    expect(document.querySelector('[data-deconstruction-question]')).not.toBeNull();

    await user.click(screen.getByRole('button', { name: /Wróć do zadania/ }));

    await screen.findByPlaceholderText('Wpisz wynik...');
    expect(screen.queryByText('Rozłożone na kroki')).not.toBeInTheDocument();
  });
});
