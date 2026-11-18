import { useState } from 'react';
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Divider, Paper, Pagination,
  Stack, TextField, Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { inboxGet, type PageResult, type Result } from '../services/inbox';
import { productError } from '../services/products';
import { InboxQueryState } from '../components/InboxQueryState';

type Bank = { bank_name: string; account_number: string; account_holder: string };
type Config = { order_timeout_seconds: number; payment_template: Bank | null };
type Faq = { id: string; question: string; answer: string; trigger_keywords: string[] };
type Connection = {
  id: string; platform: 'FACEBOOK' | 'ZALO'; account_name: string; account_id: string;
  status: 'CONNECTED' | 'DISCONNECTED' | 'ERROR'; last_error_code: string | null;
};

function Configuration({ config }: { config: Config }) {
  const client = useQueryClient();
  const [hours, setHours] = useState(config.order_timeout_seconds / 3600);
  const [bank, setBank] = useState(config.payment_template ?? { bank_name: '', account_number: '', account_holder: '' });
  const save = useMutation({
    mutationFn: async () => {
      const empty = Object.values(bank).every((value) => !value.trim());
      await api.put('/ai-config', { order_timeout_seconds: Math.round(hours * 3600), payment_template: empty ? null : bank });
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ['ai-config'] }),
  });
  return <Stack component="form" spacing={2} onSubmit={(event) => { event.preventDefault(); save.mutate(); }}>
    <Typography component="h2" variant="h6">Thu thập đơn và thông tin thanh toán</Typography>
    <TextField label="Thời gian thu thập đơn (giờ)" type="number" required value={hours}
      disabled={save.isPending} inputProps={{ min: 1, max: 72, step: 'any' }} onChange={(event) => setHours(Number(event.target.value))} />
    <TextField label="Tên ngân hàng" value={bank.bank_name} disabled={save.isPending} inputProps={{ maxLength: 100 }}
      onChange={(event) => setBank({ ...bank, bank_name: event.target.value })} />
    <TextField label="Số tài khoản" value={bank.account_number} disabled={save.isPending} inputProps={{ pattern: '[0-9]*', maxLength: 50 }}
      onChange={(event) => setBank({ ...bank, account_number: event.target.value })} />
    <TextField label="Chủ tài khoản" value={bank.account_holder} disabled={save.isPending} inputProps={{ maxLength: 100 }}
      onChange={(event) => setBank({ ...bank, account_holder: event.target.value })} />
    <Typography variant="body2" color="text.secondary">Để trống cả ba trường để gỡ thông tin thanh toán.</Typography>
    {save.isError && <Alert severity="error">{productError(save.error, 'Chưa lưu được cấu hình.')}</Alert>}
    {save.isSuccess && <Alert severity="success">Đã lưu cấu hình.</Alert>}
    <Button type="submit" variant="contained" disabled={save.isPending}>Lưu cấu hình</Button>
  </Stack>;
}

function FaqForm({ faq, close }: { faq: Faq | 'new'; close: () => void }) {
  const client = useQueryClient();
  const [question, setQuestion] = useState(faq === 'new' ? '' : faq.question);
  const [answer, setAnswer] = useState(faq === 'new' ? '' : faq.answer);
  const [keywords, setKeywords] = useState(faq === 'new' ? '' : faq.trigger_keywords.join(', '));
  const save = useMutation({
    mutationFn: async () => {
      const body = { question, answer, trigger_keywords: keywords.split(',').map((keyword) => keyword.trim()).filter(Boolean) };
      if (faq === 'new') await api.post('/ai-config/faqs', body);
      else await api.put('/ai-config/faqs/' + faq.id, body);
    },
    onSuccess: () => { void client.invalidateQueries({ queryKey: ['faqs'] }); close(); },
  });
  return <Dialog open onClose={save.isPending ? undefined : close} fullWidth maxWidth="sm" aria-labelledby="faq-title">
    <Stack component="form" onSubmit={(event) => { event.preventDefault(); save.mutate(); }}>
      <DialogTitle id="faq-title">{faq === 'new' ? 'Thêm FAQ' : 'Sửa FAQ'}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <TextField label="Câu hỏi" required value={question} disabled={save.isPending} inputProps={{ maxLength: 1000 }}
            onChange={(event) => setQuestion(event.target.value)} />
          <TextField label="Câu trả lời" required multiline minRows={3} value={answer} disabled={save.isPending}
            inputProps={{ maxLength: 5000 }} onChange={(event) => setAnswer(event.target.value)} />
          <TextField label="Từ khóa, ngăn cách bằng dấu phẩy" value={keywords} disabled={save.isPending}
            onChange={(event) => setKeywords(event.target.value)} />
          {save.isError && <Alert severity="error">{productError(save.error, 'Chưa lưu được FAQ.')}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions><Button disabled={save.isPending} onClick={close}>Đóng</Button>
        <Button type="submit" variant="contained" disabled={save.isPending}>Lưu FAQ</Button></DialogActions>
    </Stack>
  </Dialog>;
}

export function SettingsPage() {
  const client = useQueryClient();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Faq | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Faq | null>(null);
  const config = useQuery({ queryKey: ['ai-config'], queryFn: ({ signal }) => inboxGet<Result<Config>>('/ai-config', signal) });
  const faqs = useQuery({ queryKey: ['faqs', page],
    queryFn: ({ signal }) => inboxGet<PageResult<Faq>>('/ai-config/faqs', signal, { page, limit: 10 }) });
  const connections = useQuery({ queryKey: ['connections'],
    queryFn: ({ signal }) => inboxGet<Result<Connection[]>>('/connections', signal) });
  const connectionAction = useMutation({
    mutationFn: async ({ platform, disconnect }: { platform: string; disconnect: boolean }) => {
      if (disconnect) await api.delete('/connections/' + platform);
      else {
        const result = await api.post<Result<{ authorization_url: string }>>('/connections/' + platform + '/oauth/start');
        window.location.assign(result.data.data.authorization_url);
      }
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ['connections'] }),
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.delete('/ai-config/faqs/' + id),
    onSuccess: () => { setDeleting(null); setPage(1); void client.invalidateQueries({ queryKey: ['faqs'] }); },
  });
  return <Stack spacing={3}>
    <Typography component="h1" variant="h4">Cài đặt</Typography>
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Typography component="h2" variant="h6">Kết nối nền tảng</Typography>
        <InboxQueryState pending={connections.isPending} error={connections.isError} retry={() => void connections.refetch()} />
        {(['facebook', 'zalo'] as const).map((platform) => {
          const row = connections.data?.data.find((connection) => connection.platform.toLowerCase() === platform);
          const status = row?.status === 'CONNECTED' ? 'Đã kết nối' : row?.status === 'ERROR' ? 'Cần kết nối lại' : 'Chưa kết nối';
          return <Stack key={platform} spacing={1}>
            <Typography fontWeight={700}>{platform === 'facebook' ? 'Facebook Page' : 'Zalo OA'} · {status}</Typography>
            {row && <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{row.account_name} · {row.account_id}</Typography>}
            {row?.last_error_code && <Alert severity="warning">{row.last_error_code}</Alert>}
            <Stack direction="row" gap={1} flexWrap="wrap">
              <Button variant="outlined" disabled={connectionAction.isPending}
                onClick={() => connectionAction.mutate({ platform, disconnect: false })}>Kết nối {platform === 'facebook' ? 'Facebook' : 'Zalo'}</Button>
              {row?.status !== 'DISCONNECTED' && row && <Button color="error" disabled={connectionAction.isPending} onClick={() => {
                if (window.confirm('Ngắt kết nối tài khoản này?')) connectionAction.mutate({ platform, disconnect: true });
              }}>Ngắt kết nối</Button>}
            </Stack>
          </Stack>;
        })}
        {connectionAction.isError && <Alert severity="error">{productError(connectionAction.error, 'Chưa thực hiện được kết nối.')}</Alert>}
      </Stack>
    </Paper>
    <Paper variant="outlined" sx={{ p: 2 }}>
      <InboxQueryState pending={config.isPending} error={config.isError} retry={() => void config.refetch()} />
      {config.data && <Configuration config={config.data.data} />}
    </Paper>
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Stack direction="row" justifyContent="space-between"><Typography component="h2" variant="h6">FAQ</Typography>
          <Button variant="contained" onClick={() => setEditing('new')}>Thêm FAQ</Button></Stack>
        <InboxQueryState pending={faqs.isPending} error={faqs.isError} retry={() => void faqs.refetch()} />
        {faqs.data?.data.length === 0 && <Typography color="text.secondary">Chưa có FAQ.</Typography>}
        {faqs.data?.data.map((faq) => <Stack key={faq.id} spacing={1}>
          <Typography fontWeight={700} sx={{ overflowWrap: 'anywhere' }}>{faq.question}</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{faq.answer}</Typography>
          <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{faq.trigger_keywords.join(', ')}</Typography>
          <Stack direction="row" gap={1}><Button onClick={() => setEditing(faq)}>Sửa FAQ</Button>
            <Button color="error" onClick={() => { remove.reset(); setDeleting(faq); }}>Xóa FAQ</Button></Stack><Divider />
        </Stack>)}
        {faqs.data && faqs.data.meta.total > 10 && <Pagination page={page} count={Math.ceil(faqs.data.meta.total / 10)}
          onChange={(_, next) => setPage(next)} />}
      </Stack>
    </Paper>
    {editing && <FaqForm faq={editing} close={() => setEditing(null)} />}
    {deleting && <Dialog open onClose={remove.isPending ? undefined : () => setDeleting(null)} aria-labelledby="delete-faq-title">
      <DialogTitle id="delete-faq-title">Xóa FAQ</DialogTitle>
      <DialogContent><Typography sx={{ overflowWrap: 'anywhere' }}>{deleting.question}</Typography>
        {remove.isError && <Alert severity="error">Chưa xóa được FAQ.</Alert>}</DialogContent>
      <DialogActions><Button disabled={remove.isPending} onClick={() => setDeleting(null)}>Đóng</Button>
        <Button color="error" disabled={remove.isPending} onClick={() => remove.mutate(deleting.id)}>Xác nhận xóa</Button></DialogActions>
    </Dialog>}
  </Stack>;
}
