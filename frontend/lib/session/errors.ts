import type { Dispatch, SetStateAction } from 'react';

/**
 * Narrows a caught error to a message, sets it via setError, and logs it
 * with a per-call label. Internal to lib/session/ — composed by useSession().
 */
export function reportError(
  setError: Dispatch<SetStateAction<string | null>>,
  err: unknown,
  fallback: string,
  label: string
): void {
  const message = err instanceof Error ? err.message : fallback;
  setError(message);
  console.error(label, err);
}
