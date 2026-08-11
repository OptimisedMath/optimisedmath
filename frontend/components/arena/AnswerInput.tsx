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
  const currentInputMode = view.session!.current_input_mode;
  const inputMode = problem?.input_mode ?? currentInputMode;

  if (inputMode === 'radio' && problem?.answer_options) {
    return <RadioAnswerInput view={view} actions={actions} />;
  }

  return <TextAnswerInput view={view} actions={actions} />;
}

export default memo(AnswerInput);
