import { render } from '@testing-library/react';
import ThemeProvider from '@/components/ThemeProvider';
import GameArena from '@/components/arena/GameArena';

export function renderArena() {
  return render(
    <ThemeProvider>
      <GameArena />
    </ThemeProvider>
  );
}
