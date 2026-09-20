import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import TextAnswerInput from '@/components/arena/TextAnswerInput';
import { baseProblem } from './fakeBackend';

describe('TextAnswerInput exponent key (#292)', () => {
  it('does not render an exponent key when the Level cannot take a squared Unit', () => {
    render(
      <TextAnswerInput
        problem={baseProblem({ keyboard_type: 'text', exponent_key: false })}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.queryByRole('button', { name: 'x²' })).not.toBeInTheDocument();
  });

  it('renders a legible exponent key when the Level allows a squared Unit', () => {
    render(
      <TextAnswerInput
        problem={baseProblem({ keyboard_type: 'text', exponent_key: true })}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: 'x²' })).toBeInTheDocument();
  });

  it('appends the exponent character when the key is tapped', async () => {
    const user = userEvent.setup();
    render(
      <TextAnswerInput
        problem={baseProblem({ keyboard_type: 'text', exponent_key: true })}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Wpisz wynik...');
    await user.type(input, 'cm');
    await user.click(screen.getByRole('button', { name: 'x²' }));

    expect(input).toHaveValue('cm²');
  });

  it('ignores keyboard_type alone: a default-keyboard problem with exponent_key still gets the key', () => {
    render(
      <TextAnswerInput
        problem={baseProblem({ keyboard_type: 'default', exponent_key: true })}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: 'x²' })).toBeInTheDocument();
  });
});
