import { QueryClient, QueryObserver } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { tokenData } from '../test/fixtures';
import { useSession } from '../stores/session';
import { refreshSession } from '../services/api';
import { eventConsumer, startRealtime, useRealtime } from './realtime';

const sockets = vi.hoisted(() => [] as Array<{
  handlers: Map<string, (...args: unknown[]) => void>;
  any: ((name: string, event: unknown) => void) | null;
  connect: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  options: { auth: { token: string } };
  active: boolean;
}>);
vi.mock('socket.io-client', () => ({ io: vi.fn((_url, options) => {
  const socket = {
    handlers: new Map(), any: null as ((name: string, event: unknown) => void) | null,
    connect: vi.fn(), disconnect: vi.fn(), options, active: false,
    on(name: string, callback: (...args: unknown[]) => void) { this.handlers.set(name, callback); },
    onAny(callback: (name: string, event: unknown) => void) { this.any = callback; },
    offAny() { this.any = null; },
    removeAllListeners() { this.handlers.clear(); },
  };
  sockets.push(socket);
  return socket;
}) }));
vi.mock('../services/api', () => ({ refreshSession: vi.fn() }));

const conversationId = '550e8400-e29b-41d4-a716-446655440002';
let nextEvent = 0;
const event = (version: number) => ({
  schema_version: 1, event_type: 'conversation:updated',
  event_id: `00000000-0000-0000-0000-${String(++nextEvent).padStart(12, '0')}`,
  occurred_at: '2026-11-16T00:00:00Z', data: { conversation_id: conversationId, version },
});

beforeEach(() => {
  vi.useFakeTimers();
  sockets.length = 0;
  useSession.getState().clear();
  vi.mocked(refreshSession).mockReset();
});
afterEach(() => { vi.useRealTimers(); });

describe('Realtime invalidation', () => {
  it('dedupes IDs and old versions, refetches on a version gap without writing event data into cache', () => {
    const client = new QueryClient();
    client.setQueryData(['conversation', conversationId], { version: 9 });
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    const consumer = eventConsumer(client);
    const first = event(3);
    consumer.receive('conversation:updated', first);
    expect(invalidate).toHaveBeenCalledTimes(2);
    consumer.receive('conversation:updated', first);
    consumer.receive('conversation:updated', event(2));
    expect(invalidate).toHaveBeenCalledTimes(2);
    consumer.receive('conversation:updated', event(5));
    expect(invalidate).toHaveBeenCalledWith();
    expect(client.getQueryData(['conversation', conversationId])).toEqual({ version: 9 });
    client.clear();
  });

  it('dedupes a new message across event IDs and replaces an initial fetch that started before commit', async () => {
    const client = new QueryClient();
    const key = ['messages', conversationId];
    const queryFn = vi.fn()
      .mockImplementationOnce(() => new Promise(() => undefined))
      .mockResolvedValueOnce(['committed message']);
    const observer = new QueryObserver(client, { queryKey: key, queryFn });
    const unsubscribe = observer.subscribe(() => undefined);
    try {
      const invalidate = vi.spyOn(client, 'invalidateQueries');
      const consumer = eventConsumer(client);
      const data = { conversation_id: conversationId, message_id: '550e8400-e29b-41d4-a716-446655440003' };
      consumer.receive('message:new', { ...event(1), event_type: 'message:new', data });
      consumer.receive('message:new', { ...event(1), event_type: 'message:new', data });
      await vi.advanceTimersByTimeAsync(0);
      expect(queryFn).toHaveBeenCalledTimes(2);
      expect(invalidate).toHaveBeenCalledTimes(3);
      expect(client.getQueryData(key)).toEqual(['committed message']);
    } finally {
      unsubscribe();
      client.clear();
    }
  });

  it('ignores malformed IDs, recovers unsupported schemas and refetches on broker resubscription', () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    const consumer = eventConsumer(client);
    consumer.receive('conversation:updated', { ...event(1), data: { conversation_id: 'bad', version: 1 } });
    expect(invalidate).not.toHaveBeenCalled();
    consumer.receive('conversation:updated', { ...event(1), schema_version: 2 });
    consumer.receive('realtime:resync', { ...event(1), event_type: 'realtime:resync', data: {} });
    expect(invalidate).toHaveBeenCalledTimes(2);
    client.clear();
  });
});

describe('Realtime session lifecycle', () => {
  it('connects with memory auth, refetches on reconnect/focus, disconnects and cleans listeners on logout', () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    const stop = startRealtime(client);
    expect(sockets).toHaveLength(0);
    useSession.getState().accept(tokenData);
    const socket = sockets[0];
    expect(socket.options.auth.token).toBe(tokenData.access_token);
    socket.handlers.get('connect')!();
    expect(useRealtime.getState().status).toBe('connected');
    socket.handlers.get('disconnect')!('transport close');
    expect(useRealtime.getState().status).toBe('offline');
    socket.handlers.get('connect')!();
    window.dispatchEvent(new Event('focus'));
    expect(invalidate).toHaveBeenCalledTimes(3);
    useSession.getState().clear();
    expect(socket.disconnect).toHaveBeenCalledTimes(1);
    expect(socket.handlers.size).toBe(0);
    expect(socket.any).toBeNull();
    stop();
    window.dispatchEvent(new Event('focus'));
    expect(invalidate).toHaveBeenCalledTimes(3);
    client.clear();
  });

  it('refreshes through HTTP once on expired auth and avoids a refresh loop if the new token is also rejected', async () => {
    const client = new QueryClient();
    useSession.getState().accept(tokenData);
    vi.mocked(refreshSession).mockImplementation(async () => {
      const renewed = { ...tokenData, access_token: 'renewed-memory-token' };
      useSession.getState().accept(renewed);
      return renewed;
    });
    const stop = startRealtime(client);
    sockets[0].handlers.get('disconnect')!('io server disconnect');
    expect(refreshSession).toHaveBeenCalledTimes(1);
    expect(sockets).toHaveLength(2);
    expect(sockets[1].options.auth.token).toBe('renewed-memory-token');
    sockets[1].handlers.get('connect_error')!({ data: { code: 'UNAUTHORIZED' } });
    await vi.runAllTimersAsync();
    expect(refreshSession).toHaveBeenCalledTimes(1);
    stop();
    client.clear();
  });

  it('retries temporary service rejection and cancels retry timers on cleanup', async () => {
    const client = new QueryClient();
    useSession.getState().accept(tokenData);
    const stop = startRealtime(client);
    const socket = sockets[0];
    socket.handlers.get('connect_error')!({ data: { code: 'SERVICE_UNAVAILABLE' } });
    await vi.advanceTimersByTimeAsync(5000);
    expect(socket.connect).toHaveBeenCalledTimes(2);
    socket.handlers.get('connect_error')!({ data: { code: 'SERVICE_UNAVAILABLE' } });
    stop();
    await vi.advanceTimersByTimeAsync(5000);
    expect(socket.connect).toHaveBeenCalledTimes(2);
    client.clear();
  });
});
