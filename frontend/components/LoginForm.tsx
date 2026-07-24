'use client';

import { useEffect, useState } from 'react';
import { useAppNavigation } from '@/lib/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { startSession } from '@/lib/api';

const FLOATING_SYMBOLS = [
  { symbol: '∑', top: '12%', left: '10%', delay: '0s', size: 'text-5xl' },
  { symbol: 'π', top: '20%', left: '82%', delay: '0.6s', size: 'text-4xl' },
  { symbol: '÷', top: '68%', left: '8%', delay: '1.2s', size: 'text-4xl' },
  { symbol: '√', top: '78%', left: '85%', delay: '0.3s', size: 'text-5xl' },
  { symbol: '×', top: '8%', left: '52%', delay: '1.5s', size: 'text-3xl' },
  { symbol: '∞', top: '85%', left: '48%', delay: '0.9s', size: 'text-4xl' },
];

export default function LoginForm() {
  const { prefetchArena, enterArena } = useAppNavigation();
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    prefetchArena();
  }, [prefetchArena]);

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!username.trim()) {
      setError('Proszę podać imię!');
      return;
    }

    setIsLoading(true);

    try {
      const sessionResponse = await startSession({ username: username.trim() });
      localStorage.setItem('username', username.trim());
      localStorage.setItem('session_id', sessionResponse.session_id);
      enterArena();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start session';
      setError(errorMsg);
      console.error('Error starting session:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="gradient-bg relative min-h-screen overflow-hidden flex items-center justify-center p-4 text-slate-900 dark:text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        {FLOATING_SYMBOLS.map(({ symbol, top, left, delay, size }, index) => (
          <span
            key={index}
            className={`animate-float absolute select-none font-bold text-sky-500/20 dark:text-sky-300/15 ${size}`}
            style={{ top, left, animationDelay: delay }}
          >
            {symbol}
          </span>
        ))}
      </div>

      <div className="glass-card-strong animate-scale-in relative z-10 w-full max-w-md rounded-2xl p-6 sm:p-8">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl gradient-primary text-3xl shadow-lg shadow-sky-500/30">
          🧮
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-center mb-2 text-slate-900 dark:text-white">
          Optymalna nauka matematyki
        </h1>
        <h2 className="text-lg font-semibold text-center mb-6 text-slate-500 dark:text-slate-300">
          Zaloguj się
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
              Twoje imię:
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="np. Janek"
              className="bg-white/70 dark:bg-slate-900/60 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-4 focus:ring-sky-200 dark:focus:ring-sky-500/30"
              disabled={isLoading}
              autoFocus
            />
          </div>

          {error && (
            <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-200 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            className="gradient-primary w-full text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-sky-500/30 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-sky-500/40 active:translate-y-0 disabled:opacity-60 disabled:hover:translate-y-0"
          >
            {isLoading ? (
              <span className="inline-flex items-center gap-2">
                <Spinner className="h-4 w-4" />
                Ładowanie...
              </span>
            ) : (
              'Rozpocznij naukę'
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
