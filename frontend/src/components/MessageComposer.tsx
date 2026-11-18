import { useRef, useState } from 'react';
import { Alert, Button, Stack, TextField } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { productError } from '../services/products';
import { type Message, type Result } from '../services/inbox';
import { useRealtime } from '../socket/realtime';

function useMessageWrite(path: string) {
  const request = useRef<{ body: string; key: string }>();
  return async (body: object) => {
    const serialized = JSON.stringify(body);
    if (request.current?.body !== serialized) request.current = { body: serialized, key: crypto.randomUUID() };
    const response = await api.post<Result<Message>>(path, body, { headers: { 'Idempotency-Key': request.current.key } });
    request.current = undefined;
    return response.data.data;
  };
}

export function MessageComposer({ conversationId, sent }: { conversationId: string; sent: () => void }) {
  const [draft, setDraft] = useState('');
  const online = useRealtime((state) => state.status === 'connected');
  const client = useQueryClient();
  const write = useMessageWrite('/conversations/' + conversationId + '/messages');
  const send = useMutation({
    mutationFn: write,
    onSuccess: () => {
      setDraft('');
      sent();
      for (const key of ['messages', 'conversation', 'conversations']) void client.invalidateQueries({ queryKey: [key] });
    },
  });
  return <Stack component="form" spacing={1} onSubmit={(event) => {
    event.preventDefault();
    if (draft.trim() && !send.isPending && online) send.mutate({ content: draft });
  }}>
    <TextField label="Tin nhắn trả lời" multiline minRows={2} value={draft} inputProps={{ maxLength: 2000 }}
      disabled={send.isPending} onChange={(event) => setDraft(event.target.value)} />
    {send.isError && <Alert severity="error">{productError(send.error, 'Chưa xếp hàng gửi được. Nội dung vẫn được giữ.')}</Alert>}
    <Button type="submit" variant="contained" disabled={!online || !draft.trim() || send.isPending}>
      {send.isPending ? 'Đang xếp hàng…' : 'Gửi tin nhắn'}
    </Button>
  </Stack>;
}

export function MessageRetry({ message, conversationId }: { message: Message; conversationId: string }) {
  const client = useQueryClient();
  const online = useRealtime((state) => state.status === 'connected');
  const write = useMessageWrite('/conversations/' + conversationId + '/messages/' + message.id + '/retry');
  const retry = useMutation({ mutationFn: write, onSuccess: () => {
    for (const key of ['messages', 'conversation', 'conversations']) void client.invalidateQueries({ queryKey: [key] });
  } });
  if (message.sender === 'CUSTOMER' || message.status !== 'FAILED' || message.delivery_unknown) return null;
  return <Stack spacing={0.5}>
    <Button size="small" disabled={!online || retry.isPending} onClick={() => retry.mutate({})}>Thử gửi lại</Button>
    {retry.isError && <Alert severity="error">{productError(retry.error, 'Chưa gửi lại được.')}</Alert>}
  </Stack>;
}
