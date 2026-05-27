'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { startSession } from '@/lib/api';

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
    <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-800 p-6 sm:p-8 rounded-2xl shadow-2xl border border-slate-700">
        <h1 className="text-2xl sm:text-3xl font-bold text-center mb-2">🧮 Optymalna nauka matematyki :D</h1>
        <h2 className="text-xl font-semibold text-center mb-6 text-slate-300">Zaloguj się</h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
              Twoje imię:
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="np. Janek"
              className="bg-slate-900 border-slate-600 text-white placeholder:text-slate-500"
              disabled={isLoading}
              autoFocus
            />
          </div>

          {error && (
            <div className="bg-red-900 border border-red-600 text-red-200 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white font-bold py-3 rounded-lg transition-all"
          >
            {isLoading ? 'Ładowanie...' : 'Rozpocznij naukę'}
          </Button>
        </form>
      </div>
    </div>
  );
}
