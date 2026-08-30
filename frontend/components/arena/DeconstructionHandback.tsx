'use client';

import { BlockMath } from 'react-katex';
import { Button } from '@/components/ui/button';
import 'katex/dist/katex.min.css';

interface DeconstructionHandbackProps {
  question: string;
  onReturn: () => void;
}

export default function DeconstructionHandback({ question, onReturn }: DeconstructionHandbackProps) {
  return (
    <div className="animate-scale-in flex w-full max-w-lg flex-col items-center text-center">
      <div className="mb-6 text-5xl">✅</div>
      <h1 className="mb-3 text-2xl font-black text-white sm:text-3xl">Rozłożone na kroki</h1>
      <p className="mb-6 text-base text-slate-300 sm:text-lg">
        Wracasz do tego samego zadania — spróbuj jeszcze raz.
      </p>
      <div
        data-deconstruction-question
        className="mb-8 w-full rounded-2xl border border-white/10 bg-white/5 p-5 text-xl text-white sm:text-2xl"
      >
        <BlockMath math={question} />
      </div>
      <Button size="lg" onClick={onReturn} className="px-8 text-lg font-bold" autoFocus>
        Wróć do zadania ↩
      </Button>
    </div>
  );
}
