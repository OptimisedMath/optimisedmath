import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface AnswerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  showFeedback: boolean;
}

export default function AnswerInput({ value, onChange, onSubmit, disabled, showFeedback }: AnswerInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center gap-4">
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Type your answer..."
        className="px-6 py-4 text-2xl text-black rounded-lg w-64 text-center focus:outline-none focus:ring-4 focus:ring-blue-500"
        autoFocus
        disabled={showFeedback}
      />

      {!showFeedback ? (
        <Button
          type="submit"
          disabled={value.trim() === '' || disabled}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50"
        >
          Submit Answer
        </Button>
      ) : null}
    </form>
  );
}
