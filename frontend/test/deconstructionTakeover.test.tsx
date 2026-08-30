import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DECONSTRUCTION_ORDERING_SEPARATOR } from '@/lib/session';
import {
  ORDERING_STEP_ITEMS,
  TRAP_FEEDBACK,
  baseDeconstructionStep,
  baseOrderingDeconstructionStep,
  baseProblem,
  baseSession,
  wireDeconstructionTriggerFlow,
  withProblem,
  withoutCorrectAnswer,
} from './fakeBackend';
import { reachPause, reachStep } from './deconstructionFlow';
import { renderArena } from './renderArena';
import { resetStoredSession, seedStoredSession } from './testSession';

describe('Deconstruction takeover', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('holds the Trap prose on screen during the pause and taps through to the takeover', async () => {
    const client = wireDeconstructionTriggerFlow();

    await reachPause(client);
    expect(screen.getByLabelText('Przejdź dalej')).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByLabelText('Przejdź dalej'));

    await screen.findByText('Zatrzymajmy się na chwilę');
    expect(screen.queryByText(TRAP_FEEDBACK)).not.toBeInTheDocument();
  });

  it('auto-advances from the pause to the takeover after 4 seconds without a tap', async () => {
    const client = wireDeconstructionTriggerFlow();

    renderArena(client);
    await waitFor(() => {
      expect(client.startSession).toHaveBeenCalled();
      expect(client.getNextProblem).toHaveBeenCalled();
    });

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
    const step = baseDeconstructionStep({ misconception_name: 'Dodawanie ułamków wprost' });
    const client = wireDeconstructionTriggerFlow({ step });

    await reachPause(client);
    await userEvent.setup().click(screen.getByLabelText('Przejdź dalej'));

    await screen.findByText('Dodawanie ułamków wprost');
    expect(screen.getByText(/nie stracisz za to punktów ani serii/i)).toBeInTheDocument();
  });

  it('hides the original Problem behind a small header echo during the walkthrough', async () => {
    const step = baseDeconstructionStep();
    const client = wireDeconstructionTriggerFlow({ step });

    await reachStep(client, step);

    // The full Problem display (heading, input, submit row) is gone entirely —
    // not just visually covered — while only a small echo remains.
    expect(screen.queryByText('Zadanie')).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Wpisz wynik...')).not.toBeInTheDocument();
    const echo = document.querySelector('[data-deconstruction-question]');
    expect(echo).not.toBeNull();
  });

  it('renders exactly one step with progress dots and a working line that updates in place', async () => {
    const step = baseDeconstructionStep({
      step_index: 0,
      total_steps: 3,
      working_line: '\\frac{2}{3}+\\frac{1}{4}',
    });
    const client = wireDeconstructionTriggerFlow({ step });

    await reachStep(client, step);

    expect(screen.getByText('krok 1 z 3')).toBeInTheDocument();
    expect(document.querySelectorAll('[data-deconstruction-dot]').length).toBe(3);
    expect(document.querySelector('[data-deconstruction-working-line]')).not.toBeNull();
  });

  it('renders a step without a working line rather than padding it with an empty device', async () => {
    const step = baseDeconstructionStep({ working_line: null });
    const client = wireDeconstructionTriggerFlow({ step });

    await reachStep(client, step);

    expect(document.querySelector('[data-deconstruction-working-line]')).toBeNull();
  });

  it('renders the Reveal in place and still requires the Student to type the answer', async () => {
    const session = baseSession();
    const step = baseDeconstructionStep({ revealed_answer: '5/12' });
    const submitDeconstructionStep = vi.fn(async () => ({
      is_correct: true,
      feedback_msg: null,
      handback_question: null,
    }));

    const client = wireDeconstructionTriggerFlow({ session, step, submitDeconstructionStep });

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
    const step = baseDeconstructionStep();
    const client = wireDeconstructionTriggerFlow({ step });

    await reachStep(client, step);

    const exitControl = screen.getByRole('button', { name: /Zrezygnuj/ });
    expect(exitControl).toBeInTheDocument();
    expect(exitControl.className).toContain('opacity-60');
  });

  it('abandoning via the exit control returns to the arena with the Problem locked and revealed', async () => {
    const session = baseSession();
    const step = baseDeconstructionStep();
    const revealedTriggerProblem = baseProblem({ problem_id: 'prob-trigger', correct_answer: '4' });

    const abandonDeconstruction = vi.fn(async () => {
      const locked = {
        ...session,
        can_submit: false,
        can_next_problem: true,
        feedback_type: 'warning',
        feedback_msg: TRAP_FEEDBACK,
      };
      return withProblem(locked, revealedTriggerProblem);
    });

    const client = wireDeconstructionTriggerFlow({ session, step, abandonDeconstruction });

    await reachStep(client, step);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Zrezygnuj/ }));

    await waitFor(() => {
      expect(abandonDeconstruction).toHaveBeenCalledWith({ session_id: session.session_id });
    });

    await screen.findByText(TRAP_FEEDBACK);
    expect(screen.queryByText('Rozkładamy zadanie')).not.toBeInTheDocument();
    expect(screen.getByText('Poprawna odpowiedź:')).toBeInTheDocument();
  });

  it('restates the Problem on the handback screen and re-enables the same Problem on return', async () => {
    const triggerProblem = withoutCorrectAnswer(baseProblem({ problem_id: 'prob-trigger' }));
    const finalStep = baseDeconstructionStep({ step_index: 1, total_steps: 2 });

    const submitDeconstructionStep = vi.fn(async () => ({
      is_correct: true,
      feedback_msg: null,
      handback_question: triggerProblem.question,
    }));

    const client = wireDeconstructionTriggerFlow({
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

describe('Deconstruction ordering-input step (#198)', () => {
  beforeEach(() => {
    resetStoredSession();
    seedStoredSession();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the ordering control with every item instead of the typed input', async () => {
    const step = baseOrderingDeconstructionStep();
    const client = wireDeconstructionTriggerFlow({ step });

    await reachStep(client, step);

    expect(screen.queryByPlaceholderText('?')).not.toBeInTheDocument();
    const renderedItems = document.querySelectorAll('[data-deconstruction-ordering-item]');
    expect(renderedItems.length).toBe(ORDERING_STEP_ITEMS.length);
    ORDERING_STEP_ITEMS.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it('submits the reordered items joined by the ordering separator', async () => {
    const session = baseSession();
    const step = baseOrderingDeconstructionStep();
    const submitDeconstructionStep = vi.fn(async () => ({
      is_correct: true,
      feedback_msg: null,
      handback_question: null,
    }));
    const client = wireDeconstructionTriggerFlow({ session, step, submitDeconstructionStep });

    await reachStep(client, step);

    const user = userEvent.setup();
    const upButtons = screen.getAllByLabelText('Przesuń w górę');
    // Swap the first two tiers by moving the second one up.
    await user.click(upButtons[1]);
    await user.click(screen.getByRole('button', { name: 'Sprawdź' }));

    const [first, second, ...rest] = ORDERING_STEP_ITEMS;
    const expected = [second, first, ...rest].join(DECONSTRUCTION_ORDERING_SEPARATOR);

    await waitFor(() => {
      expect(submitDeconstructionStep).toHaveBeenCalledWith({
        session_id: session.session_id,
        user_input: expected,
      });
    });
  });

  it('shows the revealed order without auto-advancing, same as a typed step', async () => {
    const revealedOrder = ORDERING_STEP_ITEMS.join(DECONSTRUCTION_ORDERING_SEPARATOR);
    const step = baseOrderingDeconstructionStep({ revealed_answer: revealedOrder });
    const client = wireDeconstructionTriggerFlow({ step });

    await reachStep(client, step);

    expect(screen.getByText(revealedOrder)).toBeInTheDocument();
    expect(document.querySelectorAll('[data-deconstruction-ordering-item]').length).toBe(
      ORDERING_STEP_ITEMS.length
    );
  });
});
