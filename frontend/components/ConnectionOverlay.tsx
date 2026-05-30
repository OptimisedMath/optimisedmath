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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-md">
          <div className="glass-card-strong rounded-3xl p-8 max-w-sm mx-4 text-center animate-scale-in">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/15 flex items-center justify-center text-3xl mx-auto mb-4 border border-amber-500/30">
              🔌
            </div>
            <h2 className="text-lg font-bold mb-2 text-foreground">
              Utracono połączenie
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Nie można połączyć się z serwerem. Próbuję ponownie...
            </p>
            {retrying ? (
              <div className="flex items-center justify-center gap-2 text-primary text-sm">
                <div className="w-4 h-4 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
                Łączenie...
              </div>
            ) : (
              <button
                onClick={handleRetryNow}
                className="h-10 px-6 gradient-primary text-white rounded-xl font-semibold text-sm transition-all hover:opacity-90 shadow-lg"
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
