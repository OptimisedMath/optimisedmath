'use client';

import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import type { SessionClient } from './client';
import { httpSessionClient } from './httpSessionClient';

const SessionClientContext = createContext<SessionClient>(httpSessionClient);

export function SessionClientProvider({
  client,
  children,
}: {
  client: SessionClient;
  children: ReactNode;
}) {
  return (
    <SessionClientContext.Provider value={client}>
      {children}
    </SessionClientContext.Provider>
  );
}

export function useSessionClient(): SessionClient {
  return useContext(SessionClientContext);
}
