import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { InlineMath } from 'react-katex';
import type { Problem, GameState } from '@/lib/types';
import 'katex/dist/katex.min.css';

interface AnswerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  showFeedback: boolean;
  problem: Problem | null;
  gameState: GameState;
  onAutoSolve?: () => void;
}

export default function AnswerInput({
  value,
  onChange,
  onSubmit,
  disabled,
  showFeedback,
  problem,
  gameState,
  onAutoSolve,
}: AnswerInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim() !== '' && !disabled) {
      onSubmit();
    }
  };

  const handleRadioKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && value.trim() !== '' && !disabled && !showFeedback) {
      e.preventDefault();
      onSubmit();
    }
  };

  const inputMode = problem?.input_mode ?? gameState.current_input_mode;
  const keyboardType = problem?.keyboard_type || 'default';

  // Render radio mode
  if (inputMode === 'radio' && problem?.options) {
    return (
      <div className="flex flex-col items-center gap-4" onKeyDown={handleRadioKeyDown} tabIndex={0}>
        <div className="flex flex-col gap-3 w-full">
          {problem.options.map((option, index) => (
            <button
              key={index}
              onClick={() => !showFeedback && onChange(option)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !showFeedback) {
                  e.preventDefault();
                  onChange(option);
                  // Auto-submit after selection
                  setTimeout(() => onSubmit(), 100);
                }
              }}
              disabled={showFeedback}
              className={`p-4 text-xl rounded-lg border-2 transition-all ${
                value === option
                  ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                  : 'border-slate-600 bg-slate-700 text-slate-300 hover:border-slate-500'
              } ${showFeedback ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
            >
              {option.includes('\\') ? <InlineMath math={option} /> : option}
            </button>
          ))}
        </div>

        {!showFeedback && (
          <>
            <Button
              onClick={onSubmit}
              disabled={value.trim() === '' || disabled}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50"
            >
              Sprawdź odpowiedź
            </Button>
            {onAutoSolve && (
              <Button
                onClick={onAutoSolve}
                disabled={disabled}
                variant="outline"
                className="border-slate-500 text-slate-300 hover:bg-slate-700"
              >
                🪄 Auto-Solve
              </Button>
            )}
          </>
        )}
      </div>
    );
  }

  // Render text mode
  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Wpisz wynik..."
        inputMode={keyboardType === 'decimal' ? 'decimal' : 'text'}
        className="px-6 py-4 text-2xl text-white rounded-lg w-64 text-center focus:outline-none focus:ring-4 focus:ring-blue-500"
        autoFocus
        disabled={showFeedback}
      />

      {!showFeedback ? (
        <>
          <Button
            type="submit"
            disabled={value.trim() === '' || disabled}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50"
          >
            Sprawdź odpowiedź
          </Button>
          {onAutoSolve && (
            <Button
              onClick={onAutoSolve}
              disabled={disabled}
              variant="outline"
              className="border-slate-500 text-slate-300 hover:bg-slate-700"
            >
              🪄 Auto-Solve
            </Button>
          )}
        </>
      ) : null}
    </form>
  );
}
