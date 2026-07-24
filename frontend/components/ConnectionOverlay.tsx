'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import api from '@/lib/api';
import { Spinner } from '@/components/ui/spinner';

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
          <div className="glass-card-strong animate-scale-in rounded-2xl p-8 max-w-sm mx-4 text-center">
            <div className="gradient-xp mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl text-3xl shadow-lg shadow-amber-500/30">
              🔌
            </div>
            <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white">
              Utracono połączenie
            </h2>
            <p className="text-slate-600 dark:text-slate-300 mb-6">
              Nie można połączyć się z serwerem. Próbuję ponownie...
            </p>
            {retrying ? (
              <div className="flex items-center justify-center gap-2 text-sky-600 dark:text-sky-400">
                <Spinner className="h-5 w-5" />
                Łączenie...
              </div>
            ) : (
              <button
                onClick={handleRetryNow}
                className="gradient-primary text-white px-6 py-2 rounded-lg font-bold transition-all shadow-lg shadow-sky-500/30 hover:-translate-y-0.5 hover:shadow-xl active:translate-y-0 active:scale-[0.98]"
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
