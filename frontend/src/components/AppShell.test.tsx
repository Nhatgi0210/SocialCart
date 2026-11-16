import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { expect, it } from 'vitest';
import { AppShell } from './AppShell';
import { api } from '../services/api';
import { eventConsumer } from '../socket/realtime';
import { useSession } from '../stores/session';
import { tokenData } from '../test/fixtures';

it('refetches the unread navigation badge from API after realtime invalidation', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const mock = new MockAdapter(api);
  let total = 0;
  mock.onGet('/conversations').reply((request) => {
    expect(request.params).toEqual({ is_read: false, limit: 1 });
    return [200, { success: true, data: [], meta: { page: 1, limit: 1, total } }];
  });
  useSession.getState().accept(tokenData);
  const view = render(<QueryClientProvider client={client}><MemoryRouter
    future={{ v7_relativeSplatPath: true, v7_startTransition: true }}><AppShell /></MemoryRouter></QueryClientProvider>);
  try {
    await waitFor(() => expect(mock.history.get).toHaveLength(1));
    total = 4;
    eventConsumer(client).receive('message:new', {
      schema_version: 1, event_type: 'message:new', event_id: '550e8400-e29b-41d4-a716-446655440001',
      occurred_at: '2026-11-16T00:00:00Z', data: {
        conversation_id: '550e8400-e29b-41d4-a716-446655440002',
        message_id: '550e8400-e29b-41d4-a716-446655440003',
      },
    });
    expect(await screen.findByRole('link', { name: 'Hội thoại, 4 chưa đọc' })).toBeVisible();
  } finally {
    view.unmount();
    client.clear();
    mock.restore();
    useSession.getState().clear();
  }
});
