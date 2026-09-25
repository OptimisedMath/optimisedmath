import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { SessionClient } from '@/lib/session';
import type { DeconstructionStepResponse } from '@/lib/session/types';
import { TRAP_FEEDBACK } from './fakeBackend';
import { renderArena, waitForArenaReady } from './renderArena';

/**
 * Drives the rendered arena from a fresh session through a Deconstruction-arming
 * Submission, leaving it in the pause with the Trap Feedback still on screen.
 * Pair with a client from `wireDeconstructionTriggerFlow`.
 */
export async function reachPause(client: SessionClient): Promise<void> {
  renderArena(client);
  await waitForArenaReady(client);

  const user = userEvent.setup();
  const input = await screen.findByPlaceholderText('Wpisz wynik...');
  await user.clear(input);
  await user.type(input, '3/4');
  await user.click(screen.getByRole('button', { name: /Sprawdź odpowiedź/ }));
  await screen.findByText(TRAP_FEEDBACK);
}

/** Continues from a fresh session through the pause and intro into `step`. */
export async function reachStep(
  client: SessionClient,
  step: DeconstructionStepResponse
): Promise<void> {
  await reachPause(client);

  const user = userEvent.setup();
  await user.click(screen.getByLabelText('Przejdź dalej'));
  await screen.findByText(step.misconception_name);
  await user.click(screen.getByRole('button', { name: /Zaczynajmy/ }));
  await screen.findByText(`krok ${step.step_index + 1} z ${step.total_steps}`);
}
