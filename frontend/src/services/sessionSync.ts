import { useSession } from '../stores/session';

let channel: BroadcastChannel | null = null;

// Messages carry only invalidation, never credentials or seller data.
export function startSessionSync() {
  if (channel || typeof BroadcastChannel === 'undefined') return () => undefined;
  const connection = new BroadcastChannel('socialcart-session');
  channel = connection;
  connection.onmessage = (event: MessageEvent<unknown>) => {
    if (event.data === 'logout') useSession.getState().clear();
  };
  return () => {
    connection.close();
    if (channel === connection) channel = null;
  };
}

export function announceLogout() {
  channel?.postMessage('logout');
}

// The refresh cookie is shared between tabs. Serialize its rotation and logout.
export async function withCookieLock<T>(operation: () => Promise<T>): Promise<T> {
  return navigator.locks
    ? await navigator.locks.request('socialcart-auth-cookie', operation)
    : operation();
}
