import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import TextAnswerInput from '@/components/arena/TextAnswerInput';
import { baseProblem } from './fakeBackend';

// The echo only appears once the answer is locked, so each case has to type
// under an unlocked input first and then re-render locked.
async function typeThenLock(keyboardType: string, answer: string) {
  const user = userEvent.setup();
  const props = {
    problem: baseProblem({ keyboard_type: keyboardType }),
    adminMode: false,
    onSubmit: vi.fn(),
  };

  const { rerender } = render(
    <TextAnswerInput {...props} answerLocked={false} canSubmit={true} />
  );
  await user.type(screen.getByPlaceholderText('Wpisz wynik...'), answer);
  rerender(<TextAnswerInput {...props} answerLocked={true} canSubmit={false} />);
}

function katexOutput() {
  return document.querySelector('.katex');
}

describe('TextAnswerInput answer echo routing (#291)', () => {
  it('echoes a Unit answer as plain upright text with the space intact', async () => {
    await typeThenLock('text', '126 mm²');

    expect(screen.getByText('126 mm²')).toBeInTheDocument();
    expect(katexOutput()).not.toBeInTheDocument();
  });

  it('still renders a mixed-fraction answer as maths', async () => {
    await typeThenLock('default', '1 2/3');

    expect(katexOutput()).toBeInTheDocument();
  });

  it('leaves a spaceless, slashless answer unchanged', async () => {
    await typeThenLock('default', '42');

    expect(screen.getByText('42')).toBeInTheDocument();
    expect(katexOutput()).not.toBeInTheDocument();
  });
});
