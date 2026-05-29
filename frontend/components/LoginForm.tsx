'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { startSession } from '@/lib/api';

const FLOATING_SYMBOLS = [
  { symbol: 'π', x: 10, y: 15, delay: 0, size: 'text-3xl' },
  { symbol: '∑', x: 85, y: 10, delay: 0.5, size: 'text-4xl' },
  { symbol: '∫', x: 75, y: 75, delay: 1, size: 'text-3xl' },
  { symbol: '√', x: 15, y: 70, delay: 1.5, size: 'text-2xl' },
  { symbol: '∞', x: 50, y: 5, delay: 2, size: 'text-3xl' },
  { symbol: 'Δ', x: 90, y: 45, delay: 0.8, size: 'text-2xl' },
  { symbol: 'θ', x: 5, y: 45, delay: 1.2, size: 'text-2xl' },
  { symbol: '÷', x: 60, y: 85, delay: 1.8, size: 'text-3xl' },
];

export default function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
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
      router.push('/arena');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start session';
      setError(errorMsg);
      console.error('Error starting session:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen gradient-bg-light dark:gradient-bg-dark flex items-center justify-center p-4 relative overflow-hidden">
      {FLOATING_SYMBOLS.map((item, i) => (
        <span
          key={i}
          className={`absolute ${item.size} text-indigo-300/20 dark:text-indigo-400/10 select-none animate-float`}
          style={{
            left: `${item.x}%`,
            top: `${item.y}%`,
            animationDelay: `${item.delay}s`,
            animationDuration: `${3 + item.delay}s`,
          }}
        >
          {item.symbol}
        </span>
      ))}

      <div className="w-full max-w-md glass-card-strong p-8 sm:p-10 rounded-3xl animate-fade-slide-up relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center text-3xl mb-4 shadow-lg glow-primary">
            🧮
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-center text-foreground">
            Optimised Math
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Zaloguj się, aby kontynuować naukę</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-muted-foreground mb-2">
              Twoje imię
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="np. Janek"
              className="h-12 px-4 text-base bg-white/50 dark:bg-white/5 border-border/50 focus-visible:border-primary focus-visible:ring-primary/30 rounded-xl transition-all"
              disabled={isLoading}
              autoFocus
            />
          </div>

          {error && (
            <div className="bg-destructive/10 border border-destructive/30 text-destructive px-4 py-3 rounded-xl text-sm animate-fade-slide-in">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full h-12 gradient-primary hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-xl text-base transition-all shadow-lg hover:shadow-xl hover:translate-y-[-1px] active:translate-y-0"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
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
