'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import api from '@/lib/api';

export default function ConnectionOverlay({ children }: { children: React.ReactNode }) {
  const [disconnected, setDisconnected] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const id = api.interceptors.response.use(
      (response) => {
        setDisconnected(false);
        return response;
      },
      (error) => {
        if (!error.response && (error.code === 'ERR_NETWORK' || error.message === 'Network Error')) {
          setDisconnected(true);
        }
        return Promise.reject(error);
      }
    );
    return () => {
      api.interceptors.response.eject(id);
    };
  }, []);

  useEffect(() => {
    if (!disconnected) return;

    const poll = async () => {
      setRetrying(true);
      try {
        await api.get('/health');
        setDisconnected(false);
        window.location.reload();
      } catch {
        retryTimer.current = setTimeout(poll, 5000);
      } finally {
        setRetrying(false);
      }
    };

    retryTimer.current = setTimeout(poll, 3000);
    return () => {
      if (retryTimer.current) clearTimeout(retryTimer.current);
    };
  }, [disconnected]);

  const handleRetryNow = useCallback(async () => {
    if (retryTimer.current) clearTimeout(retryTimer.current);
    setRetrying(true);
    try {
      await api.get('/health');
      setDisconnected(false);
      window.location.reload();
    } catch {
      setRetrying(false);
    }
  }, []);

  return (
    <>
      {children}
      {disconnected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-8 max-w-sm mx-4 text-center shadow-2xl border border-slate-200 dark:border-slate-700">
            <div className="text-4xl mb-4">🔌</div>
            <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white">
              Utracono połączenie
            </h2>
            <p className="text-slate-600 dark:text-slate-300 mb-6">
              Nie można połączyć się z serwerem. Próbuję ponownie...
            </p>
            {retrying ? (
              <div className="flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Łączenie...
              </div>
            ) : (
              <button
                onClick={handleRetryNow}
                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition-colors"
              >
                Spróbuj ponownie
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
}
