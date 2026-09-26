'use client';

import Link from 'next/link';
import { ROUTES } from '@/lib/routes';
import { clearSessionStorage, getStoredSessionId, useSessionClient } from '@/lib/session';

interface LogoutLinkProps {
  className?: string;
  children?: React.ReactNode;
}

export default function LogoutLink({
  className,
  children = 'Wyloguj',
}: LogoutLinkProps) {
  const client = useSessionClient();

  return (
    <Link
      href={ROUTES.login}
      replace
      prefetch
      className={className}
      onNavigate={() => {
        const sessionId = getStoredSessionId();
        if (sessionId) {
          // Not awaited, so navigation to the login screen stays immediate:
          // a lost race leaves an unreachable row, which is exactly the
          // outcome of not deleting at all (ADR-0019).
          client.endSession({ session_id: sessionId }).catch(() => {});
        }
        clearSessionStorage();
      }}
    >
      {children}
    </Link>
  );
}
