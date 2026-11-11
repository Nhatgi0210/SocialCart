import { useState } from 'react';
import { Alert, Button, Chip, Divider, Link, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink } from 'react-router-dom';
import { api } from '../services/api';
import { inboxGet, localTime, platforms, type CustomerDetail, type Result } from '../services/inbox';
import { InboxQueryState } from './InboxQueryState';

export function CustomerProfile({ id }: { id: string }) {
  const client = useQueryClient();
  const [draft, setDraft] = useState('');
  const key = ['customer', id];
  const profile = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => inboxGet<Result<CustomerDetail>>('/customers/' + id, signal),
  });
  const save = useMutation({
    mutationFn: (content: string) => api.post('/customers/' + id + '/notes', { content }),
    onSuccess: async () => {
      setDraft('');
      await client.invalidateQueries({ queryKey: key });
    },
  });
  const remove = useMutation({
    mutationFn: (noteId: string) => api.delete('/customers/' + id + '/notes/' + noteId),
    onSuccess: () => client.invalidateQueries({ queryKey: key }),
  });
  const detail = profile.data?.data;

  return <Stack spacing={2} sx={{ minWidth: 0 }}>
    <InboxQueryState pending={profile.isPending} error={profile.isError} retry={() => void profile.refetch()} />
    {detail && !profile.isError && <>
      <Stack direction="row" alignItems="center" flexWrap="wrap" gap={1}>
        <Typography component="h2" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{detail.customer.name}</Typography>
        <Chip label={platforms[detail.customer.platform]} size="small" />
      </Stack>
      <Typography color="text.secondary" variant="body2">Hồ sơ từ {localTime(detail.customer.created_at)}</Typography>
      <Divider />
      <Typography component="h3" fontWeight={700}>Hội thoại ({detail.conversation_ids.length})</Typography>
      {detail.conversation_ids.length === 0 && <Typography color="text.secondary">Chưa có hội thoại.</Typography>}
      {detail.conversation_ids.map((conversationId, index) => <Link key={conversationId} component={RouterLink}
        to={'/inbox?conversation=' + conversationId}>Hội thoại {index + 1}</Link>)}
      <Typography component="h3" fontWeight={700}>Đơn hàng ({detail.order_ids.length})</Typography>
      {detail.order_ids.length === 0 && <Typography color="text.secondary">Chưa có đơn hàng.</Typography>}
      {detail.order_ids.map((orderId, index) => <Link key={orderId} component={RouterLink}
        to={'/orders/' + orderId}>Đơn hàng {index + 1}</Link>)}
      <Divider />
      <Typography component="h3" fontWeight={700}>Ghi chú</Typography>
      <Stack component="form" spacing={1} onSubmit={(event) => {
        event.preventDefault();
        if (draft.trim() && !save.isPending) save.mutate(draft.trim());
      }}>
        <TextField label="Thêm ghi chú" multiline minRows={2} value={draft} disabled={save.isPending}
          onChange={(event) => setDraft(event.target.value)} inputProps={{ maxLength: 5000 }} />
        <Button type="submit" variant="contained" disabled={!draft.trim() || save.isPending}>
          {save.isPending ? 'Đang lưu…' : 'Lưu ghi chú'}
        </Button>
        {save.isError && <Alert severity="error">Chưa lưu được ghi chú. Vui lòng thử lại.</Alert>}
      </Stack>
      {remove.isError && <Alert severity="error">Chưa xóa được ghi chú. Vui lòng thử lại.</Alert>}
      {detail.notes.length === 0 && <Typography color="text.secondary">Chưa có ghi chú.</Typography>}
      {detail.notes.map((note) => <Stack key={note.id} spacing={0.5}>
        <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{note.content}</Typography>
        <Typography variant="caption" color="text.secondary">{localTime(note.created_at)}</Typography>
        <Button size="small" color="error" sx={{ alignSelf: 'flex-start' }} disabled={remove.isPending}
          onClick={() => { if (window.confirm('Xóa ghi chú này?')) remove.mutate(note.id); }}>Xóa ghi chú</Button>
        <Divider />
      </Stack>)}
    </>}
  </Stack>;
}
