import { Button } from '@/components/ui/button';
import type { Feedback } from '@/lib/types';

interface FeedbackCardProps {
  feedback: Feedback | null;
  onNextProblem: () => void;
}

export default function FeedbackCard({ feedback, onNextProblem }: FeedbackCardProps) {
  if (!feedback) {
    return null;
  }

  return (
    <div className="w-full flex flex-col items-center gap-4 mt-4">
      <div className={`text-2xl font-bold ${feedback.correct ? 'text-green-400' : 'text-red-400'}`}>
        {feedback.message}
      </div>
      <Button
        type="button"
        onClick={onNextProblem}
        className="bg-slate-700 hover:bg-slate-600 text-white px-8 py-3 rounded-lg text-xl font-bold transition-all"
      >
        Next Problem ➡️
      </Button>
    </div>
  );
}
