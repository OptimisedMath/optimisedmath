import { BlockMath } from 'react-katex';
import type { Problem } from '@/lib/types';
import 'katex/dist/katex.min.css';

interface ProblemDisplayProps {
  problem: Problem | null;
  selectedMacro: string | null;
  isLoading?: boolean;
}

export default function ProblemDisplay({ problem, selectedMacro, isLoading }: ProblemDisplayProps) {
  if (isLoading) {
    return (
      <div className="text-2xl text-slate-400 animate-pulse">
        Loading problem...
      </div>
    );
  }

  if (!problem) {
    return null;
  }

  return (
    <div className="mb-6 text-slate-300">
      <p className="text-sm uppercase tracking-wide">{selectedMacro}</p>
      <h2 className="text-3xl font-medium">Solve this:</h2>
      <div className="text-5xl font-bold mb-8 p-4 bg-slate-700 rounded-lg">
        <BlockMath math={problem.question} />
      </div>
    </div>
  );
}
