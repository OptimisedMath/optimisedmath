import { render } from '@testing-library/react';
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
