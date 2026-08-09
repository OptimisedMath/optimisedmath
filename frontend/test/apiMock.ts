import { vi } from 'vitest';

type PostHandler = (body: unknown) => unknown;
type GetHandler = (params: Record<string, unknown> | undefined) => unknown;

const state = vi.hoisted(() => {
  const postHandlers = new Map<string, PostHandler>();
  const getHandlers = new Map<string, GetHandler>();

  const mockApi = {
    post: vi.fn(async (url: string, body?: unknown) => {
      const handler = postHandlers.get(url);
      if (!handler) {
        throw new Error(`Unhandled POST ${url}`);
      }
      return { data: handler(body) };
    }),
    get: vi.fn(async (url: string, config?: { params?: Record<string, unknown> }) => {
      const handler = getHandlers.get(url);
      if (!handler) {
        throw new Error(`Unhandled GET ${url}`);
      }
      return { data: handler(config?.params) };
    }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };

  return { mockApi, postHandlers, getHandlers };
});

export const mockApi = state.mockApi;

export function resetFakeBackend() {
  state.postHandlers.clear();
  state.getHandlers.clear();
  state.mockApi.post.mockClear();
  state.mockApi.get.mockClear();
}

export function onPost(path: string, handler: PostHandler) {
  state.postHandlers.set(path, handler);
}

export function onGet(path: string, handler: GetHandler) {
  state.getHandlers.set(path, handler);
}
