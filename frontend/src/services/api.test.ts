import MockAdapter from 'axios-mock-adapter';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { api, authTransport, login, logout, refreshSession } from './api';
import { useSession } from '../stores/session';
import { tokenData } from '../test/fixtures';

let backend: MockAdapter;
let auth: MockAdapter;
beforeEach(() => {
  useSession.getState().clear();
  backend = new MockAdapter(api);
  auth = new MockAdapter(authTransport);
});
afterEach(() => { backend.restore(); auth.restore(); });

describe('Gateway API client (simulated HTTP)', () => {
  it('uses the Gateway prefix once, cookie credentials and memory-only login', async () => {
    auth.onPost('/auth/login', { email: tokenData.user.email, password: 'test-only' }).reply(200, { success: true, data: tokenData });
    await login(tokenData.user.email, 'test-only');
    backend.onGet('/auth/me').reply((config) => {
      expect(config.baseURL).toBe('http://localhost:8000/api/v1');
      expect(config.headers?.Authorization).toBe(`Bearer ${tokenData.access_token}`);
      expect(config.withCredentials).toBe(true);
      return [200, { success: true, data: tokenData.user }];
    });
    await api.get('/auth/me');
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it('coalesces concurrent refreshes into one cookie rotation', async () => {
    auth.onPost('/auth/refresh').reply(200, { success: true, data: tokenData });
    await Promise.all([refreshSession(), refreshSession(), refreshSession()]);
    expect(auth.history.post).toHaveLength(1);
    expect(useSession.getState().status).toBe('authenticated');
  });

  it('renews one time for simultaneous expired access requests', async () => {
    useSession.getState().accept({ ...tokenData, access_token: 'expired' });
    auth.onPost('/auth/refresh').reply(200, { success: true, data: tokenData });
    backend.onGet('/orders').reply((config) => config.headers?.Authorization === 'Bearer expired' ? [401] : [200, { success: true, data: [] }]);
    await Promise.all([api.get('/orders'), api.get('/orders')]);
    expect(auth.history.post).toHaveLength(1);
    expect(backend.history.get).toHaveLength(4);
  });

  it('stops retrying when the renewed token is rejected', async () => {
    useSession.getState().accept(tokenData);
    auth.onPost('/auth/refresh').reply(200, { success: true, data: tokenData });
    backend.onGet('/orders').reply(401);
    await expect(api.get('/orders')).rejects.toThrow();
    expect(auth.history.post).toHaveLength(1);
    expect(backend.history.get).toHaveLength(2);
    expect(useSession.getState().status).toBe('anonymous');
  });

  it('fails closed on Redis/upstream failure without retrying refresh', async () => {
    useSession.getState().accept(tokenData);
    backend.onGet('/orders').reply(401);
    auth.onPost('/auth/refresh').reply(503);
    await expect(api.get('/orders')).rejects.toThrow();
    expect(auth.history.post).toHaveLength(1);
    expect(useSession.getState().status).toBe('error');
    expect(useSession.getState().accessToken).toBeNull();
  });

  it('does not revive a session from refresh arriving after logout', async () => {
    useSession.getState().accept(tokenData);
    let complete!: (result: [number, unknown]) => void;
    auth.onPost('/auth/refresh').reply(() => new Promise((resolve) => { complete = resolve; }));
    auth.onPost('/auth/logout').reply(204);
    const refresh = refreshSession();
    const result = expect(refresh).rejects.toThrow('Session changed');
    await logout();
    complete([200, { success: true, data: tokenData }]);
    await result;
    expect(useSession.getState().status).toBe('anonymous');
  });

  it('preserves the session if logout cannot revoke the server cookie', async () => {
    useSession.getState().accept(tokenData);
    auth.onPost('/auth/logout').reply(503);
    await expect(logout()).rejects.toThrow();
    expect(useSession.getState().status).toBe('authenticated');
  });
});
