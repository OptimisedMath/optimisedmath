'use client';

import { BlockMath } from 'react-katex';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import DeconstructionExitControl from './DeconstructionExitControl';
import 'katex/dist/katex.min.css';

interface DeconstructionIntroProps {
  headerQuestion: string | null;
  misconceptionName: string | null;
  isLoading: boolean;
  onBegin: () => void;
  onExit: () => void;
}

export default function DeconstructionIntro({
  headerQuestion,
  misconceptionName,
  isLoading,
  onBegin,
  onExit,
}: DeconstructionIntroProps) {
  return (
    <div className="animate-scale-in flex w-full max-w-lg flex-col items-center text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-3xl bg-sky-500/15 text-3xl">
        🧩
      </div>
      <h1 className="mb-3 text-2xl font-black text-white sm:text-3xl">Zatrzymajmy się na chwilę</h1>
      <p className="mb-2 text-base text-slate-300 sm:text-lg">
        To zadanie rozłożymy razem na kroki. Nie stracisz za to punktów ani serii.
      </p>
      {misconceptionName && (
        <p className="mb-6 text-sm font-semibold uppercase tracking-[0.16em] text-sky-300">
          {misconceptionName}
        </p>
      )}
      {headerQuestion && (
        <div
          data-deconstruction-question
          className="mb-8 w-full overflow-x-auto rounded-2xl border border-white/10 bg-white/5 p-5 text-base text-white sm:text-xl"
        >
          <BlockMath math={headerQuestion} />
        </div>
      )}
      {isLoading ? (
        <div className="mb-4 flex items-center gap-2 text-slate-400">
          <Spinner className="h-5 w-5" />
          <span>Przygotowujemy kroki...</span>
        </div>
      ) : (
        <Button size="lg" onClick={onBegin} className="mb-4 px-8 text-lg font-bold" autoFocus>
          Zaczynajmy →
        </Button>
      )}
      <DeconstructionExitControl onExit={onExit} />
    </div>
  );
}
