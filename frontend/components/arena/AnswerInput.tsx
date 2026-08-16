'use client';

import { memo } from 'react';
import type { SessionActions, SessionView } from '@/lib/session';
import RadioAnswerInput from './RadioAnswerInput';
import TextAnswerInput from './TextAnswerInput';

interface AnswerInputProps {
  view: SessionView;
  actions: SessionActions;
}

function AnswerInput({
  view,
  actions,
}: AnswerInputProps) {
  const problem = view.problem;
  const inputMode = view.currentInputMode;
  const answerLocked = view.feedbackPhase === 'answer_locked';

  if (inputMode === 'radio' && problem?.answer_options) {
    return (
      <RadioAnswerInput view={view} actions={actions} answerLocked={answerLocked} />
    );
  }

  return (
    <TextAnswerInput view={view} actions={actions} answerLocked={answerLocked} />
  );
}

export default memo(AnswerInput);
