import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import TextAnswerInput from '@/components/arena/TextAnswerInput';
import type { Problem } from '@/lib/session';
import { baseProblem } from './fakeBackend';

function renderInput(overrides: Partial<Problem>) {
  render(
    <TextAnswerInput
      problem={baseProblem(overrides)}
      answerLocked={false}
      canSubmit={true}
      adminMode={false}
      onSubmit={vi.fn()}
    />
  );
}

const exponentKey = () => screen.queryByRole('button', { name: 'x²' });

describe('TextAnswerInput exponent key (#292)', () => {
  it('does not render an exponent key when the Level cannot take a squared Unit', () => {
    renderInput({ keyboard_type: 'text', exponent_key: false });

    expect(exponentKey()).not.toBeInTheDocument();
  });

  it('labels the exponent key `x²` when the Level allows a squared Unit', () => {
    renderInput({ keyboard_type: 'text', exponent_key: true });

    expect(exponentKey()).toBeInTheDocument();
  });

  it('appends the exponent character when the key is tapped', async () => {
    const user = userEvent.setup();
    renderInput({ keyboard_type: 'text', exponent_key: true });

    const input = screen.getByPlaceholderText('Wpisz wynik...');
    await user.type(input, 'cm');
    await user.click(screen.getByRole('button', { name: 'x²' }));

    expect(input).toHaveValue('cm²');
  });

  it('adds the exponent key alongside the default keyboard keys rather than replacing them', () => {
    renderInput({ keyboard_type: 'default', exponent_key: true });

    expect(exponentKey()).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'spacja' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '/' })).toBeInTheDocument();
  });
});
