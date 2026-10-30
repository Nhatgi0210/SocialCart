import { useEffect } from 'react';
import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material';
import { Navigate, Outlet } from 'react-router-dom';
import { refreshSession } from '../services/api';
import { useSession } from '../stores/session';

export function SessionGate() {
  const status = useSession((s) => s.status);
  useEffect(() => {
    if (status === 'initializing') void refreshSession().catch(() => undefined);
  }, [status]);

  if (status === 'initializing') return <Box component="main" sx={{ minHeight: '100dvh', display: 'grid', placeItems: 'center' }}>
    <Stack alignItems="center" spacing={2} role="status">
      <CircularProgress aria-label="Đang kiểm tra phiên đăng nhập" />
      <Typography>Đang kiểm tra phiên đăng nhập…</Typography>
    </Stack>
  </Box>;
  if (status === 'error') return <Stack component="main" spacing={2} sx={{ maxWidth: 480, mx: 'auto', p: 3, mt: 8 }}>
    <Alert severity="error">Chưa thể kiểm tra phiên đăng nhập. Vui lòng thử lại.</Alert>
    <Button variant="contained" onClick={() => {
      useSession.setState({ status: 'initializing' });
    }}>Thử lại</Button>
  </Stack>;
  return <Outlet />;
}

export function ProtectedRoute() {
  const status = useSession((s) => s.status);
  return status === 'authenticated' ? <Outlet /> : <Navigate to="/login" replace />;
}
