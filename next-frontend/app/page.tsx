import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-8 font-sans">
      <div className="text-center max-w-2xl">
        <h1 className="text-5xl font-bold mb-6 text-yellow-400">
          Optimised Math Learning
        </h1>
        <p className="text-xl mb-8 text-slate-300">
          Master math through focus and flow state
        </p>
        <Link href="/arena">
          <Button className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-lg text-xl font-bold transition-all shadow-lg hover:shadow-blue-500/50">
            Start Learning 🚀
          </Button>
        </Link>
      </div>
    </div>
  );
}
