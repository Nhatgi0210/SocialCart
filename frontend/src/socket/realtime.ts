import { io } from 'socket.io-client';
import type { QueryClient, QueryKey } from '@tanstack/react-query';
import { create } from 'zustand';
import { refreshSession } from '../services/api';
import { useSession } from '../stores/session';

export const useRealtime = create<{ status: 'connecting' | 'connected' | 'offline' }>(() => ({ status: 'connecting' }));
const events = ['message:new', 'message:updated', 'conversation:updated', 'order:created', 'order:updated', 'dashboard:stats:updated', 'realtime:resync'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export function eventConsumer(client: QueryClient) {
  const seen = new Set<string>();
  const versions = new Map<string, number>();
  const newMessages = new Set<string>();
  const invalidate = (queryKey?: QueryKey) => {
    // The first fetch can still be returning a snapshot from before the event.
    void client.cancelQueries({ queryKey, predicate: (query) => query.state.data === undefined });
    void (queryKey ? client.invalidateQueries({ queryKey }) : client.invalidateQueries());
  };
  const resync = () => invalidate();
  return {
    resync,
    receive(name: string, raw: unknown) {
      if (!events.includes(name) || !raw || typeof raw !== 'object') return;
      const event = raw as Record<string, unknown>;
      if (event.schema_version !== 1) { resync(); return; }
      if (event.event_type !== name || typeof event.event_id !== 'string' || !uuid.test(event.event_id)
        || typeof event.occurred_at !== 'string' || !Number.isFinite(Date.parse(event.occurred_at))
        || !event.data || typeof event.data !== 'object') return;
      const data = event.data as Record<string, unknown>;
      const ids = name.startsWith('message:') ? ['conversation_id', 'message_id']
        : name.startsWith('order:') ? ['order_id', 'conversation_id']
          : name === 'conversation:updated' ? ['conversation_id'] : [];
      if (ids.some((id) => typeof data[id] !== 'string' || !uuid.test(data[id]))) return;
      const versioned = name.startsWith('order:') || name === 'conversation:updated';
      if (versioned && (typeof data.version !== 'number' || !Number.isSafeInteger(data.version) || data.version < 1)) return;
      if (seen.has(event.event_id)) return;
      seen.add(event.event_id);
      if (seen.size > 1000) seen.delete(seen.values().next().value!);
      if (name === 'message:new' && typeof data.message_id === 'string') {
        if (newMessages.has(data.message_id)) return;
        newMessages.add(data.message_id);
        if (newMessages.size > 1000) newMessages.delete(newMessages.values().next().value!);
      }
      if (versioned) {
        const key = name.startsWith('order:') ? `order:${data.order_id}` : `conversation:${data.conversation_id}`;
        const previous = versions.get(key);
        if (previous !== undefined && (data.version as number) <= previous) return;
        if (previous !== undefined && (data.version as number) > previous + 1) resync();
        versions.delete(key);
        versions.set(key, data.version as number);
        if (versions.size > 1000) versions.delete(versions.keys().next().value!);
      }
      if (name === 'realtime:resync' || name === 'dashboard:stats:updated') { resync(); return; }
      const keys: unknown[][] = [['conversations'], ['conversation', data.conversation_id]];
      if (name.startsWith('message:')) keys.push(['messages', data.conversation_id]);
      if (name.startsWith('order:')) keys.push(['orders'], ['order', data.order_id], ['products'], ['product'], ['customer'], ['dashboard']);
      keys.forEach((queryKey) => invalidate(queryKey));
    },
  };
}

export function startRealtime(client: QueryClient) {
  let stopSocket = () => {};
  let currentToken: string | null = null;
  let authFailures = 0;
  let userId: string | undefined;
  let consumer = eventConsumer(client);
  function sync() {
    const session = useSession.getState();
    const token = session.status === 'authenticated' ? session.accessToken : null;
    if (token === currentToken) return;
    stopSocket();
    currentToken = token;
    if (session.user?.id !== userId) {
      userId = session.user?.id;
      authFailures = 0;
      consumer = eventConsumer(client);
    }
    if (!token) { useRealtime.setState({ status: 'offline' }); return; }
    useRealtime.setState({ status: 'connecting' });
    const socket = io(import.meta.env.VITE_SOCKET_URL || 'http://localhost:8009', {
      autoConnect: false, auth: { token }, reconnectionDelay: 1000, reconnectionDelayMax: 10_000,
    });
    let disposed = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const renew = () => {
      if (disposed || authFailures >= 1) return;
      authFailures += 1;
      void refreshSession().catch(() => undefined);
    };
    socket.on('connect', () => {
      authFailures = 0;
      useRealtime.setState({ status: 'connected' });
      consumer.resync();
    });
    socket.onAny((name: string, event: unknown) => consumer.receive(name, event));
    socket.on('connect_error', (error: Error & { data?: { code?: string } }) => {
      useRealtime.setState({ status: 'offline' });
      if (error.data?.code === 'UNAUTHORIZED') renew();
      else if (!socket.active) timer = setTimeout(() => { if (!disposed) socket.connect(); }, 5000);
    });
    socket.on('disconnect', (reason) => {
      useRealtime.setState({ status: 'offline' });
      if (reason === 'io server disconnect') renew();
    });
    stopSocket = () => {
      disposed = true;
      clearTimeout(timer);
      socket.removeAllListeners();
      socket.offAny();
      socket.disconnect();
    };
    socket.connect();
  }
  const unsubscribe = useSession.subscribe(sync);
  const resume = () => {
    if (useSession.getState().status === 'authenticated') consumer.resync();
  };
  window.addEventListener('online', resume);
  window.addEventListener('focus', resume);
  sync();
  return () => {
    unsubscribe();
    stopSocket();
    window.removeEventListener('online', resume);
    window.removeEventListener('focus', resume);
  };
}
