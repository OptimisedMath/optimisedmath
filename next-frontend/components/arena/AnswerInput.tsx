import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import type { Problem, GameState } from '@/lib/types';

interface AnswerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  showFeedback: boolean;
  problem: Problem | null;
  gameState: GameState;
  onAutoSolve?: () => void;
  adminMode?: boolean;
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
  adminMode = false,
}: AnswerInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const inputMode = gameState.current_input_mode;
  const keyboardType = problem?.keyboard_type || 'default';

  // Render radio mode
  if (inputMode === 'radio' && problem?.options) {
    return (
      <div className="flex flex-col items-center gap-4">
        <div className="flex flex-col gap-3 w-full">
          {problem.options.map((option, index) => (
            <button
              key={index}
              onClick={() => !showFeedback && onChange(option)}
              disabled={showFeedback}
              className={`p-4 text-xl rounded-lg border-2 transition-all ${
                value === option
                  ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                  : 'border-slate-600 bg-slate-700 text-slate-300 hover:border-slate-500'
              } ${showFeedback ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
            >
              {option.includes('\\') ? `$${option}$` : option}
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
            {adminMode && onAutoSolve && (
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
        placeholder="Wpisz wynik..."
        inputMode={keyboardType === 'decimal' ? 'decimal' : 'text'}
        className="px-6 py-4 text-2xl text-black rounded-lg w-64 text-center focus:outline-none focus:ring-4 focus:ring-blue-500"
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
          {adminMode && onAutoSolve && (
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
