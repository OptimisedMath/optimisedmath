import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import TextAnswerInput from '@/components/arena/TextAnswerInput';
import { baseProblem } from './fakeBackend';

describe('TextAnswerInput answer echo routing', () => {
  it('echoes a Unit answer as plain upright text with the space intact', async () => {
    const user = userEvent.setup();
    const problem = baseProblem({ keyboard_type: 'text' });

    const { rerender } = render(
      <TextAnswerInput
        problem={problem}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    await user.type(screen.getByPlaceholderText('Wpisz wynik...'), '126 mm²');

    rerender(
      <TextAnswerInput
        problem={problem}
        answerLocked={true}
        canSubmit={false}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByText('126 mm²')).toBeInTheDocument();
    expect(document.querySelector('.katex')).not.toBeInTheDocument();
  });

  it('still renders a mixed-fraction answer as maths', async () => {
    const user = userEvent.setup();
    const problem = baseProblem({ keyboard_type: 'default' });

    const { rerender } = render(
      <TextAnswerInput
        problem={problem}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    await user.type(screen.getByPlaceholderText('Wpisz wynik...'), '1 2/3');

    rerender(
      <TextAnswerInput
        problem={problem}
        answerLocked={true}
        canSubmit={false}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    expect(document.querySelector('.katex')).toBeInTheDocument();
  });

  it('leaves a spaceless, slashless answer unchanged', async () => {
    const user = userEvent.setup();
    const problem = baseProblem({ keyboard_type: 'default' });

    const { rerender } = render(
      <TextAnswerInput
        problem={problem}
        answerLocked={false}
        canSubmit={true}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    await user.type(screen.getByPlaceholderText('Wpisz wynik...'), '42');

    rerender(
      <TextAnswerInput
        problem={problem}
        answerLocked={true}
        canSubmit={false}
        adminMode={false}
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByText('42')).toBeInTheDocument();
    expect(document.querySelector('.katex')).not.toBeInTheDocument();
  });
});
