import { StrictMode } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material';
import { MemoryRouter, useLocation, useRoutes } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { routes } from './router';
import { theme } from './theme';
import { useSession } from './stores/session';
import { authTransport } from './services/api';
import { tokenData } from './test/fixtures';

let auth: MockAdapter;
beforeEach(() => {
  useSession.getState().clear();
  auth = new MockAdapter(authTransport);
});
afterEach(() => auth.restore());

function open(path: string) {
  render(<StrictMode><ThemeProvider theme={theme}>
    <MemoryRouter initialEntries={[path]} future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <RouteView />
    </MemoryRouter>
  </ThemeProvider></StrictMode>);
}

function RouteView() {
  const content = useRoutes(routes);
  const location = useLocation();
  return <><output aria-label="Test pathname">{location.pathname}</output>{content}</>;
}

describe('Auth shell (simulated HTTP)', () => {
  it.each(['/dashboard', '/inbox', '/customers/123', '/orders/123', '/settings'])('protects direct navigation to %s', async (path) => {
    open(path);
    expect(await screen.findByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible();
    expect(screen.getByLabelText('Test pathname')).toHaveTextContent('/login');
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });

  it('renders loading then redirects to login when no refresh cookie exists', async () => {
    useSession.setState({ status: 'initializing' });
    auth.onPost('/auth/refresh').reply(401);
    open('/inbox');
    expect(screen.getByRole('progressbar', { name: 'Đang kiểm tra phiên đăng nhập' })).toBeVisible();
    expect(await screen.findByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible();
    expect(auth.history.post).toHaveLength(1);
  });

  it('offers recovery after bootstrap failure and never exposes protected content', async () => {
    useSession.setState({ status: 'initializing' });
    auth.onPost('/auth/refresh').replyOnce(503);
    auth.onPost('/auth/refresh').reply(401);
    open('/dashboard');
    expect(await screen.findByRole('alert')).toHaveTextContent('Chưa thể kiểm tra phiên');
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible();
  });

  it('validates inline, retains email on rejection, and prevents duplicate submits', async () => {
    open('/login');
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));
    expect(screen.getByText('Nhập địa chỉ email hợp lệ.')).toBeVisible();
    expect(screen.getByText('Nhập mật khẩu của bạn.')).toBeVisible();
    expect(auth.history.post).toHaveLength(0);
    await user.type(screen.getByRole('textbox', { name: /Email/ }), tokenData.user.email);
    await user.type(screen.getByLabelText(/Mật khẩu/), 'wrong-test-password');
    let reject!: (value: [number]) => void;
    auth.onPost('/auth/login').reply(() => new Promise((resolve) => { reject = resolve; }));
    await user.dblClick(screen.getByRole('button', { name: 'Đăng nhập' }));
    expect(screen.getByRole('button', { name: 'Đang đăng nhập…' })).toBeDisabled();
    expect(auth.history.post).toHaveLength(1);
    reject([401]);
    expect(await screen.findByRole('alert')).toHaveTextContent('Email hoặc mật khẩu không đúng.');
    expect(screen.getByRole('textbox', { name: /Email/ })).toHaveValue(tokenData.user.email);
  });

  it('opens the seller shell after login and leaves it after successful logout', async () => {
    auth.onPost('/auth/login').reply(200, { success: true, data: tokenData });
    auth.onPost('/auth/logout').reply(204);
    open('/login');
    const user = userEvent.setup();
    await user.type(screen.getByRole('textbox', { name: /Email/ }), tokenData.user.email);
    await user.type(screen.getByLabelText(/Mật khẩu/), 'test-only{Enter}');
    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeVisible();
    expect(screen.getByLabelText('Test pathname')).toHaveTextContent('/dashboard');
    expect(screen.getByText(/Chủ shop thử nghiệm/)).toBeVisible();
    expect(screen.getByText('Không gian làm việc đang được chuẩn bị')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Đăng xuất' }));
    await waitFor(() => expect(screen.getByLabelText('Test pathname')).toHaveTextContent('/login'));
    expect(useSession.getState().accessToken).toBeNull();
  });
});
