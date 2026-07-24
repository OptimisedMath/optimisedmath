import { useEffect } from 'react';

export function useDocumentKeydown(handler: (e: KeyboardEvent) => void, deps: unknown[]) {
  useEffect(() => {
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- caller controls deps explicitly
  }, deps);
}
