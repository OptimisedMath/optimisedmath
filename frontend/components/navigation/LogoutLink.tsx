'use client';

import Link from 'next/link';
import { ROUTES } from '@/lib/routes';
import { clearSessionStorage } from '@/lib/session';

interface LogoutLinkProps {
  className?: string;
  children?: React.ReactNode;
}

export default function LogoutLink({
  className,
  children = 'Wyloguj',
}: LogoutLinkProps) {
  return (
    <Link
      href={ROUTES.login}
      replace
      prefetch
      className={className}
      onNavigate={() => {
        clearSessionStorage();
      }}
    >
      {children}
    </Link>
  );
}
