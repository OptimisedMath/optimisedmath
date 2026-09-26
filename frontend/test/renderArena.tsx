import { render, screen, waitFor } from '@testing-library/react';
import { expect } from 'vitest';
import ThemeProvider from '@/components/ThemeProvider';
import { SessionClientProvider, type SessionClient } from '@/lib/session';
import GameArena from '@/components/arena/GameArena';
import { createFakeSessionClient } from './fakeBackend';

export function renderArena(client: SessionClient = createFakeSessionClient()) {
  return render(
    <ThemeProvider>
      <SessionClientProvider client={client}>
        <GameArena />
      </SessionClientProvider>
    </ThemeProvider>
  );
}

/** Settles the arena's bootstrap — start, first Problem, loading placeholder gone. */
export async function waitForArenaReady(client: SessionClient) {
  await waitFor(() => {
    expect(client.startSession).toHaveBeenCalled();
    expect(client.getNextProblem).toHaveBeenCalled();
  });
  await waitFor(() => {
    expect(screen.queryByText('Ładowanie zadania...')).not.toBeInTheDocument();
  });
}
