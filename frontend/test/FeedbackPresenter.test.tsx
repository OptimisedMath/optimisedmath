import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import FeedbackPresenter from '@/components/arena/FeedbackPresenter';
import {
  emptySessionDisplayProjection,
  type Feedback,
  type SessionActions,
  type SessionView,
} from '@/lib/session';
import { baseProblem, baseSession } from './fakeBackend';

function baseView(overrides: Partial<SessionView> = {}): SessionView {
  const session = baseSession();
  const problem = baseProblem();
  return {
    needsLogin: false,
    isLoading: false,
    error: null,
    isNavigating: false,
    isSubmitting: false,
    isLoadingNextProblem: false,
    canSubmit: true,
    canNextProblem: false,
    feedbackPhase: 'none',
    session,
    problem,
    feedback: null,
    selectedChapterName: 'Ułamki',
    topicName: 'Dodawanie',
    adminMode: false,
    ...emptySessionDisplayProjection(),
    ...overrides,
  };
}

const noopActions: SessionActions = {
  submit: vi.fn(),
  navigate: vi.fn(),
  nextProblem: vi.fn(),
  reset: vi.fn(),
  clearErrorAndReload: vi.fn(),
};

function softErrorFeedback(message = 'Zły format odpowiedzi'): Feedback {
  return {
    correct: false,
    message,
    feedback_type: 'info',
    answer_locked: false,
  };
}

function answerLockedFeedback(
  message: string,
  correct: boolean,
  feedback_type: 'success' | 'warning'
): Feedback {
  return {
    correct,
    message,
    feedback_type,
    answer_locked: true,
  };
}

describe('FeedbackPresenter', () => {
  it('renders nothing when feedbackPhase is none', () => {
    const { container } = render(
      <FeedbackPresenter view={baseView()} actions={noopActions} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the soft error box for soft_error phase', () => {
    render(
      <FeedbackPresenter
        view={baseView({
          feedbackPhase: 'soft_error',
          feedback: softErrorFeedback(),
        })}
        actions={noopActions}
      />
    );

    const softError = screen.getByText('Zły format odpowiedzi');
    expect(softError).toHaveAttribute('data-feedback-type', 'info');
    expect(softError.className).toContain('border-amber-200');
    expect(softError.className).toContain('text-amber-700');
    expect(screen.queryByRole('button', { name: /Następne zadanie/ })).not.toBeInTheDocument();
  });

  it('renders FeedbackCard with success styling for answer_locked correct phase', () => {
    render(
      <FeedbackPresenter
        view={baseView({
          feedbackPhase: 'answer_locked',
          canNextProblem: true,
          feedback: answerLockedFeedback('Brawo!', true, 'success'),
        })}
        actions={noopActions}
      />
    );

    const badge = screen.getByText('Brawo!');
    expect(badge).toHaveAttribute('data-feedback-type', 'success');
    expect(badge.className).toContain('bg-emerald-100');
    expect(screen.getByRole('button', { name: /Następne zadanie/ })).toBeInTheDocument();
  });

  it('renders FeedbackCard with warning styling for answer_locked wrong phase', () => {
    render(
      <FeedbackPresenter
        view={baseView({
          feedbackPhase: 'answer_locked',
          canNextProblem: true,
          feedback: answerLockedFeedback('Wrong feedback', false, 'warning'),
        })}
        actions={noopActions}
      />
    );

    const badge = screen.getByText('Wrong feedback');
    expect(badge).toHaveAttribute('data-feedback-type', 'warning');
    expect(badge.className).toContain('bg-red-100');
    expect(screen.getByRole('button', { name: /Następne zadanie/ })).toBeInTheDocument();
  });
});
