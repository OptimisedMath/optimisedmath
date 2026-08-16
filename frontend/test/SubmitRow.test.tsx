import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import SubmitRow from '@/components/arena/SubmitRow';

describe('SubmitRow', () => {
  it('calls onSubmit when the submit button is clicked', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <SubmitRow
        onSubmit={onSubmit}
        submitDisabled={false}
        showAutoSolve={false}
        autoSolveDisabled={false}
        onAutoSolve={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: /Sprawdź odpowiedź/ }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('disables the submit button when submitDisabled is true', () => {
    render(
      <SubmitRow
        onSubmit={vi.fn()}
        submitDisabled={true}
        showAutoSolve={false}
        autoSolveDisabled={false}
        onAutoSolve={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Sprawdź odpowiedź/ })).toBeDisabled();
  });

  it('does not render the auto-solve button when showAutoSolve is false', () => {
    render(
      <SubmitRow
        onSubmit={vi.fn()}
        submitDisabled={false}
        showAutoSolve={false}
        autoSolveDisabled={false}
        onAutoSolve={vi.fn()}
      />
    );

    expect(screen.queryByRole('button', { name: /Auto-Solve/ })).not.toBeInTheDocument();
  });

  it('calls onAutoSolve when the auto-solve button is clicked and reflects autoSolveDisabled', async () => {
    const user = userEvent.setup();
    const onAutoSolve = vi.fn();

    render(
      <SubmitRow
        onSubmit={vi.fn()}
        submitDisabled={false}
        showAutoSolve={true}
        autoSolveDisabled={false}
        onAutoSolve={onAutoSolve}
      />
    );

    const autoSolveButton = screen.getByRole('button', { name: /Auto-Solve/ });
    expect(autoSolveButton).not.toBeDisabled();
    await user.click(autoSolveButton);
    expect(onAutoSolve).toHaveBeenCalledTimes(1);
  });

  it('disables the auto-solve button when autoSolveDisabled is true', () => {
    render(
      <SubmitRow
        onSubmit={vi.fn()}
        submitDisabled={false}
        showAutoSolve={true}
        autoSolveDisabled={true}
        onAutoSolve={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Auto-Solve/ })).toBeDisabled();
  });

  it('renders the submit button as type="submit" when submitType is "submit" and does not require onSubmit', () => {
    render(
      <SubmitRow
        submitType="submit"
        submitDisabled={false}
        showAutoSolve={false}
        autoSolveDisabled={false}
        onAutoSolve={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Sprawdź odpowiedź/ })).toHaveAttribute(
      'type',
      'submit'
    );
  });

  it('defaults the submit button to type="button" when submitType is not provided', () => {
    render(
      <SubmitRow
        onSubmit={vi.fn()}
        submitDisabled={false}
        showAutoSolve={false}
        autoSolveDisabled={false}
        onAutoSolve={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Sprawdź odpowiedź/ })).toHaveAttribute(
      'type',
      'button'
    );
  });
});
