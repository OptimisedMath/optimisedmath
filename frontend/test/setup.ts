import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { createElement } from 'react';
import { afterEach, vi } from 'vitest';

const routerMocks = vi.hoisted(() => ({
  prefetch: vi.fn(),
  replace: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => routerMocks,
}));

vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    className,
    onNavigate,
  }: {
    children: React.ReactNode;
    href: string;
    className?: string;
    onNavigate?: () => void;
  }) =>
    createElement(
      'a',
      {
        href,
        className,
        onClick: () => onNavigate?.(),
      },
      children
    ),
}));

afterEach(() => {
  cleanup();
});
