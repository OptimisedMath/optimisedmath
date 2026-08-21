import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import FeedbackCard from '@/components/arena/FeedbackCard';
import type { Feedback } from '@/lib/session';
import { baseProblem } from './fakeBackend';

function correctFeedback(message = 'Brawo!'): Feedback {
  return { correct: true, message, feedback_type: 'success' };
}

function wrongFeedback(message = 'Zła odpowiedź'): Feedback {
  return { correct: false, message, feedback_type: 'warning' };
}

describe('FeedbackCard', () => {
  it('renders the default Next-problem label with no confetti', () => {
    render(
      <FeedbackCard
        feedback={correctFeedback()}
        problem={baseProblem()}
        inputMode="input"
        topicCompleted={false}
        levelCompleted={false}
        hasNextUnlockedTopic={true}
        disabled={false}
        onNextProblem={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Następne zadanie/ })).toBeInTheDocument();
    expect(screen.queryByText('🎉')).not.toBeInTheDocument();
  });

  it('shows confetti and the Next-level label when levelCompleted is true', () => {
    render(
      <FeedbackCard
        feedback={correctFeedback()}
        problem={baseProblem()}
        inputMode="input"
        topicCompleted={false}
        levelCompleted={true}
        hasNextUnlockedTopic={true}
        disabled={false}
        onNextProblem={vi.fn()}
      />
    );

    expect(screen.getByText('🎉')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Następny poziom/ })).toBeInTheDocument();
  });

  it('shows the Next-topic label when topicCompleted is true and another topic is Reachable', () => {
    render(
      <FeedbackCard
        feedback={correctFeedback()}
        problem={baseProblem()}
        inputMode="input"
        topicCompleted={true}
        levelCompleted={false}
        hasNextUnlockedTopic={true}
        disabled={false}
        onNextProblem={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /Następny temat/ })).toBeInTheDocument();
  });

  it('shows the congratulations message with no button when the topic is completed with nothing left Reachable', () => {
    render(
      <FeedbackCard
        feedback={correctFeedback()}
        problem={baseProblem()}
        inputMode="input"
        topicCompleted={true}
        levelCompleted={false}
        hasNextUnlockedTopic={false}
        disabled={false}
        onNextProblem={vi.fn()}
      />
    );

    expect(screen.getByText(/Ukończyłeś wszystkie tematy/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Następn/ })).not.toBeInTheDocument();
  });

  it('reveals the correct answer for a wrong text-mode submission', () => {
    render(
      <FeedbackCard
        feedback={wrongFeedback()}
        problem={baseProblem({ correct_answer: '4' })}
        inputMode="input"
        topicCompleted={false}
        levelCompleted={false}
        hasNextUnlockedTopic={true}
        disabled={false}
        onNextProblem={vi.fn()}
      />
    );

    expect(screen.getByText('Poprawna odpowiedź:')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('does not reveal a correct-answer banner in radio mode', () => {
    render(
      <FeedbackCard
        feedback={wrongFeedback()}
        problem={baseProblem({ correct_answer: '4', answer_options: ['1', '2', '3', '4'] })}
        inputMode="radio"
        topicCompleted={false}
        levelCompleted={false}
        hasNextUnlockedTopic={true}
        disabled={false}
        onNextProblem={vi.fn()}
      />
    );

    expect(screen.queryByText('Poprawna odpowiedź:')).not.toBeInTheDocument();
  });
});
