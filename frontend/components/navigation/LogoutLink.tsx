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
          // Unawaited: a lost race leaves an unreachable row, the same
          // outcome as not deleting at all, so it never delays navigation.
          client.endSession({ session_id: sessionId }).catch(() => {});
        }
        clearSessionStorage();
      }}
    >
      {children}
    </Link>
  );
}
