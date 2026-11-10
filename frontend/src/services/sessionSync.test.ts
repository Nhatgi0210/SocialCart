import { afterEach, expect, it, vi } from 'vitest';
import { announceLogout, startSessionSync, withCookieLock } from './sessionSync';
import { useSession } from '../stores/session';
import { tokenData } from '../test/fixtures';

afterEach(() => vi.unstubAllGlobals());

it('clears memory on remote logout and sends no tokens in the channel', () => {
  const close = vi.fn();
  const postMessage = vi.fn();
  const connection = { onmessage: null as null | ((event: MessageEvent) => void), close, postMessage };
  vi.stubGlobal('BroadcastChannel', class { constructor() { return connection; } });
  const stop = startSessionSync();
  useSession.getState().accept(tokenData);
  connection.onmessage?.(new MessageEvent('message', { data: 'unknown' }));
  expect(useSession.getState().status).toBe('authenticated');
  connection.onmessage?.(new MessageEvent('message', { data: 'logout' }));
  expect(useSession.getState().accessToken).toBeNull();
  expect(useSession.getState().user).toBeNull();
  announceLogout();
  expect(postMessage).toHaveBeenCalledExactlyOnceWith('logout');
  stop();
  expect(close).toHaveBeenCalledOnce();
});

it('serializes cookie operations through the same browser lock', async () => {
  const request = vi.fn(async (_name: string, operation: () => Promise<string>) => operation());
  vi.stubGlobal('navigator', { locks: { request } });
  expect(await withCookieLock(async () => 'done')).toBe('done');
  expect(request).toHaveBeenCalledWith('socialcart-auth-cookie', expect.any(Function));
});

it('keeps single-tab operation available without Web Locks', async () => {
  vi.stubGlobal('navigator', {});
  expect(await withCookieLock(async () => 'done')).toBe('done');
});
