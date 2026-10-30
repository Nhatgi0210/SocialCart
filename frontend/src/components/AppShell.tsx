import { useState } from 'react';
import { Alert, Box, Button, Divider, Stack, Typography } from '@mui/material';
import { NavLink, Outlet } from 'react-router-dom';
import { Brand } from './Brand';
import { logout } from '../services/api';
import { queryClient } from '../services/queryClient';
import { useSession } from '../stores/session';

const links = [['/dashboard', 'Tổng quan'], ['/inbox', 'Hội thoại'], ['/customers', 'Khách hàng'], ['/products', 'Sản phẩm'], ['/orders', 'Đơn hàng'], ['/settings', 'Cài đặt']];

export function AppShell() {
  const user = useSession((s) => s.user);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(false);

  async function signOut() {
    setPending(true);
    setError(false);
    try {
      await logout();
      queryClient.clear();
    } catch {
      setError(true);
    } finally {
      setPending(false);
    }
  }

  return <Box sx={{ minHeight: '100dvh' }}>
    <Button component="a" href="#main-content" sx={{ position: 'absolute', left: -9999, '&:focus': { left: 16, top: 8, zIndex: 10, bgcolor: 'white' } }}>Đến nội dung chính</Button>
    <Stack component="header" direction="row" alignItems="center" justifyContent="space-between" gap={2} sx={{ px: { xs: 2, md: 4 }, py: 2, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider' }}>
      <Brand />
      <Button variant="outlined" disabled={pending} onClick={() => void signOut()}>{pending ? 'Đang đăng xuất…' : 'Đăng xuất'}</Button>
    </Stack>
    <Box sx={{ display: { md: 'grid' }, gridTemplateColumns: '224px minmax(0, 1fr)' }}>
      <Stack component="nav" aria-label="Điều hướng chính" direction={{ xs: 'row', md: 'column' }} gap={1} sx={{ p: 2, overflowX: 'auto', borderRight: { md: '1px solid' }, borderColor: { md: 'divider' } }}>
        {links.map(([path, label]) => <Button key={path} component={NavLink} to={path} sx={{ justifyContent: 'flex-start', whiteSpace: 'nowrap', px: 2, color: 'text.secondary', '&.active': { bgcolor: '#e9f5f1', color: 'primary.dark' } }}>{label}</Button>)}
      </Stack>
      <Box component="main" id="main-content" tabIndex={-1} sx={{ p: { xs: 3, md: 5 }, maxWidth: 1120, width: '100%' }}>
        {error && <Alert severity="error" sx={{ mb: 3 }}>Chưa thể đăng xuất. Vui lòng thử lại.</Alert>}
        <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{user?.name} · {user?.email}</Typography>
        <Divider sx={{ my: 3 }} />
        <Outlet />
      </Box>
    </Box>
  </Box>;
}
