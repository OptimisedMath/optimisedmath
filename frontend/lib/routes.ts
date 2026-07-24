export const ROUTES = {
  home: '/',
  login: '/login',
  arena: '/arena',
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];
