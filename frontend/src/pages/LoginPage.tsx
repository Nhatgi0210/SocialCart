import { useRef, useState, type FormEvent } from 'react';
import { Alert, Box, Button, Chip, Paper, Stack, TextField, Typography } from '@mui/material';
import ArrowForward from '@mui/icons-material/ArrowForward';
import { Navigate } from 'react-router-dom';
import { Brand } from '../components/Brand';
import { login, loginError } from '../services/api';
import { useSession } from '../stores/session';

export function LoginPage() {
  const status = useSession((s) => s.status);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const submitting = useRef(false);
  const invalidEmail = !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  if (status === 'authenticated') return <Navigate to="/dashboard" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitted(true);
    if (invalidEmail || !password || submitting.current) return;
    submitting.current = true;
    setPending(true);
    setError('');
    try {
      await login(email.trim(), password);
    } catch (reason) {
      setError(loginError(reason));
    } finally {
      setPending(false);
      submitting.current = false;
    }
  }

  return <Box component="main" sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
    <Box component="header" sx={{ px: { xs: 3, md: 6 }, py: 3 }}><Brand /></Box>
    <Box sx={{ flex: 1, display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, alignItems: 'center', gap: { xs: 4, md: 8 }, maxWidth: 1120, width: '100%', mx: 'auto', px: { xs: 3, md: 5 }, py: 5 }}>
      <Stack spacing={3} sx={{ maxWidth: 480 }}>
        <Chip label="Dành cho cửa hàng của bạn" sx={{ alignSelf: 'flex-start', bgcolor: '#e9f5f1', color: 'primary.dark', fontWeight: 500 }} />
        <Typography component="p" sx={{ fontSize: { xs: 34, md: 52 }, fontWeight: 600, lineHeight: 1.12, letterSpacing: '-1.5px' }}>
          Gần khách hàng hơn.<br /><Box component="span" sx={{ color: 'primary.dark' }}>Gọn việc bán hàng.</Box>
        </Typography>
        <Typography color="text.secondary" fontSize={18} lineHeight={1.7}>
          Một nơi để theo dõi hội thoại Facebook, Zalo và chăm sóc từng đơn hàng.
        </Typography>
        <Stack direction="row" spacing={1}>
          <Chip variant="outlined" label="Facebook Page" />
          <Chip variant="outlined" label="Zalo OA" />
        </Stack>
      </Stack>
      <Paper sx={{ p: { xs: 3, sm: 5 }, border: '1px solid', borderColor: 'divider', boxShadow: '0 12px 48px #29252408', width: '100%', maxWidth: 440, justifySelf: { md: 'end' } }}>
        <Typography component="h1" variant="h1" mb={1}>Chào mừng trở lại</Typography>
        <Typography color="text.secondary" mb={4}>Đăng nhập để quản lý cửa hàng của bạn.</Typography>
        <Stack component="form" aria-label="Đăng nhập" noValidate onSubmit={(e) => void submit(e)} spacing={2.5}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField id="email" label="Email" name="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} error={submitted && invalidEmail} helperText={submitted && invalidEmail ? 'Nhập địa chỉ email hợp lệ.' : undefined} disabled={pending} />
          <TextField id="password" label="Mật khẩu" name="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} error={submitted && !password} helperText={submitted && !password ? 'Nhập mật khẩu của bạn.' : undefined} disabled={pending} />
          <Button type="submit" variant="contained" size="large" disabled={pending} endIcon={!pending && <ArrowForward />} aria-busy={pending}>
            {pending ? 'Đang đăng nhập…' : 'Đăng nhập'}
          </Button>
        </Stack>
      </Paper>
    </Box>
    <Typography component="footer" color="text.secondary" variant="body2" sx={{ px: 3, py: 3, textAlign: 'center' }}>SocialCart · Đồng hành cùng cửa hàng nhỏ</Typography>
  </Box>;
}
