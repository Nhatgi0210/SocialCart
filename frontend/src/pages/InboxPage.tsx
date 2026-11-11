import { useEffect, useRef, useState } from 'react';
import { Alert, Avatar, Box, Button, Chip, Divider, List, ListItemButton, MenuItem, Pagination, Paper, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useSearchParams } from 'react-router-dom';
import { CustomerProfile } from '../components/CustomerProfile';
import { InboxQueryState } from '../components/InboxQueryState';
import { api } from '../services/api';
import {
  aiStatuses, inboxGet, localTime, platforms, statuses, type AIStatus, type Conversation, type Message, type PageResult, type Result, type Status,
} from '../services/inbox';

function Chat({ id, back }: { id: string; back: () => void }) {
  const [page, setPage] = useState(1);
  const [showProfile, setShowProfile] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const readAttempted = useRef(false);
  const client = useQueryClient();
  const path = '/conversations/' + id;
  const detailKey = ['conversation', id];
  const detail = useQuery({
    queryKey: detailKey,
    queryFn: ({ signal }) => inboxGet<Result<Conversation>>(path, signal),
  });
  const messages = useQuery({
    queryKey: ['messages', id, page],
    queryFn: ({ signal }) => inboxGet<PageResult<Message>>(path + '/messages', signal, { page, limit: 20 }),
    enabled: detail.isSuccess,
  });
  const update = useMutation({
    mutationFn: async ({ route, body }: { route: string; body: object }) =>
      (await api.patch<Result<Conversation>>(path + route, body)).data,
    onSuccess: (result) => {
      client.setQueryData(detailKey, result);
      return client.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        return Promise.all([client.invalidateQueries({ queryKey: detailKey }),
          client.invalidateQueries({ queryKey: ['conversations'] })]);
      }
    },
  });
  const conversation = detail.data?.data;
  const { mutate } = update;
  const markRead = () => mutate({ route: '/read', body: { is_read: true } });
  useEffect(() => { heading.current?.focus(); }, []);
  useEffect(() => {
    if (conversation?.is_read === false && !readAttempted.current) {
      readAttempted.current = true;
      mutate({ route: '/read', body: { is_read: true } });
    }
  }, [conversation?.is_read, mutate]);

  const list = messages.data;
  const conflict = axios.isAxiosError(update.error) && update.error.response?.status === 409;
  const sender = { CUSTOMER: 'Khách hàng', AI: 'AI', SELLER: 'Người bán' };
  return <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', lg: 'minmax(0, 1fr) minmax(220px, 0.65fr)' }, gap: 2 }}>
    <Paper variant="outlined" sx={{ p: 2, minWidth: 0 }}>
      <Stack spacing={2}>
        <Button sx={{ display: { xs: 'inline-flex', lg: 'none' }, alignSelf: 'flex-start' }} onClick={back}>Về danh sách</Button>
        <Typography ref={heading} tabIndex={-1} component="h2" variant="h6" sx={{ overflowWrap: 'anywhere' }}>
          {conversation?.customer.name ?? 'Chi tiết hội thoại'}
        </Typography>
        <InboxQueryState pending={detail.isPending} error={detail.isError} retry={() => void detail.refetch()} />
        {conversation && !detail.isError && <>
          <Stack direction="row" gap={1} flexWrap="wrap">
            <Chip label={platforms[conversation.platform]} size="small" />
            <Chip label={aiStatuses[conversation.ai_status]} size="small" color={conversation.ai_status === 'NEEDS_SELLER' ? 'warning' : 'default'} />
            {!conversation.is_read && <Chip label="Chưa đọc" size="small" color="primary" />}
          </Stack>
          {conversation.ai_status === 'NEEDS_SELLER' && <Alert severity="warning">Hội thoại này đang chờ bạn tiếp quản.</Alert>}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <TextField select size="small" label="Trạng thái xử lý" value={conversation.status} disabled={update.isPending}
              sx={{ minWidth: 140 }} onChange={(event) => mutate({ route: '/status', body: {
                status: event.target.value as Status, expected_version: conversation.version,
              } })}>
              {Object.entries(statuses).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
            </TextField>
            <Button variant="outlined" disabled={update.isPending} onClick={() => mutate({ route: '/ai-status', body: {
              ai_status: conversation.ai_status === 'SELLER_HANDLING' ? 'AI_HANDLING' : 'SELLER_HANDLING',
              expected_version: conversation.version,
            } })}>
              {conversation.ai_status === 'SELLER_HANDLING' ? 'Bật lại AI' : conversation.ai_status === 'NEEDS_SELLER' ? 'Tiếp quản' : 'Tắt AI'}
            </Button>
            <Button sx={{ display: { lg: 'none' } }} aria-expanded={showProfile} aria-controls="inbox-customer-profile"
              onClick={() => setShowProfile((value) => !value)}>{showProfile ? 'Ẩn thông tin khách' : 'Thông tin khách'}</Button>
          </Stack>
          {update.isError && <Alert severity={conflict ? 'warning' : 'error'}
            action={update.variables?.route === '/read' ? <Button color="inherit" onClick={markRead}>Thử lại</Button> : undefined}>
            {conflict ? 'Hội thoại đã thay đổi. Hãy kiểm tra trạng thái hiện tại rồi thử lại.' : 'Chưa cập nhật được hội thoại. Vui lòng thử lại.'}
          </Alert>}
          <Divider />
          <Typography component="h3" fontWeight={700}>Tin nhắn</Typography>
          <InboxQueryState pending={messages.isPending} error={messages.isError} retry={() => void messages.refetch()} />
          {list && !messages.isError && <>
            {list.data.length === 0 && <Typography color="text.secondary">Chưa có tin nhắn.</Typography>}
            <Stack component="ul" aria-label="Lịch sử tin nhắn" spacing={1.5} sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {list.data.map((message) => <Box component="li" key={message.id} sx={{
                borderRadius: 2, p: 1.5, maxWidth: '90%', alignSelf: message.sender === 'CUSTOMER' ? 'flex-start' : 'flex-end',
                bgcolor: message.sender === 'AI' ? 'rgba(15,118,110,0.10)' : 'action.hover',
              }}>
                <Typography variant="caption" fontWeight={700}>{sender[message.sender]} · {localTime(message.created_at)}</Typography>
                <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{message.content}</Typography>
                {(message.delivery_unknown || message.status !== 'SENT') && <Typography variant="caption"
                  color={message.status === 'FAILED' ? 'error' : 'text.secondary'}>
                  {message.delivery_unknown ? 'Chưa xác nhận được kết quả gửi' : message.status === 'FAILED' ? 'Gửi thất bại' : 'Đang gửi'}
                </Typography>}
              </Box>)}
            </Stack>
            {list.meta.total > list.meta.limit && <Pagination aria-label="Phân trang tin nhắn" page={page}
              count={Math.ceil(list.meta.total / list.meta.limit)} onChange={(_, next) => setPage(next)} />}
          </>}
        </>}
      </Stack>
    </Paper>
    {conversation && !detail.isError && <Paper id="inbox-customer-profile" component="aside" aria-label="Thông tin khách"
      variant="outlined" sx={{ p: 2, minWidth: 0, display: { xs: showProfile ? 'block' : 'none', lg: 'block' } }}>
      <CustomerProfile key={conversation.customer.id} id={conversation.customer.id} />
    </Paper>}
  </Box>;
}

export function InboxPage() {
  const [params, setParams] = useSearchParams();
  const selected = params.get('conversation');
  const listHeading = useRef<HTMLHeadingElement>(null);
  const previousSelection = useRef(selected);
  useEffect(() => {
    if (!selected && previousSelection.current) listHeading.current?.focus();
    previousSelection.current = selected;
  }, [selected]);
  const [page, setPage] = useState(1);
  const [platform, setPlatform] = useState('');
  const [status, setStatus] = useState('');
  const [aiStatus, setAiStatus] = useState<AIStatus | ''>('');
  const query = useQuery({
    queryKey: ['conversations', page, platform, status, aiStatus],
    queryFn: ({ signal }) => inboxGet<PageResult<Conversation>>('/conversations', signal, {
      page, limit: 10, platform: platform || undefined, status: status || undefined, ai_status: aiStatus || undefined,
    }),
  });
  const result = query.data;
  return <Stack spacing={2}>
    <Typography component="h1" variant="h4">Hội thoại</Typography>
    <Box sx={{ display: { xs: 'block', lg: 'grid' }, gridTemplateColumns: 'minmax(240px, 320px) minmax(0, 1fr)', gap: 2 }}>
      <Paper variant="outlined" sx={{ p: 2, display: { xs: selected ? 'none' : 'block', lg: 'block' } }}>
        <Stack spacing={1.5}>
          <Typography ref={listHeading} tabIndex={-1} component="h2" variant="h6">Danh sách hội thoại</Typography>
          <TextField select size="small" label="Nền tảng" value={platform}
            onChange={(event) => { setPlatform(event.target.value); setPage(1); }}>
            <MenuItem value="">Tất cả nền tảng</MenuItem>
            {Object.entries(platforms).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <TextField select size="small" label="Trạng thái" value={status}
            onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
            <MenuItem value="">Tất cả trạng thái</MenuItem>
            {Object.entries(statuses).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <TextField select size="small" label="Trạng thái AI" value={aiStatus}
            onChange={(event) => { setAiStatus(event.target.value as AIStatus | ''); setPage(1); }}>
            <MenuItem value="">Tất cả trạng thái AI</MenuItem>
            {Object.entries(aiStatuses).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <InboxQueryState pending={query.isPending} error={query.isError} retry={() => void query.refetch()} />
          {result && !query.isError && <>
            {result.data.length === 0 && <Typography color="text.secondary">
              {platform || status || aiStatus ? 'Không có hội thoại nào khớp bộ lọc.' : 'Chưa có hội thoại.'}
            </Typography>}
            <List disablePadding aria-label="Danh sách hội thoại">
              {result.data.map((conversation) => <ListItemButton key={conversation.id} component="button" selected={selected === conversation.id}
                aria-pressed={selected === conversation.id}
                onClick={() => setParams({ conversation: conversation.id })} sx={{ width: '100%', gap: 1, px: 1, alignItems: 'flex-start' }}>
                <Avatar aria-hidden="true" sx={{ width: 32, height: 32, fontSize: 14, mt: 0.5 }}>
                  {conversation.customer.name.replace(/^\[Demo\]\s*/, '').slice(0, 1).toUpperCase()}
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                  <Typography noWrap fontWeight={conversation.is_read ? 500 : 800}>{conversation.customer.name}</Typography>
                  <Typography noWrap variant="body2" color="text.secondary">{conversation.last_message_preview || 'Chưa có tin nhắn'}</Typography>
                  <Stack direction="row" flexWrap="wrap" gap={0.5} sx={{ my: 0.5 }}>
                    <Chip size="small" label={platforms[conversation.platform]} />
                    {!conversation.is_read && <Chip size="small" color="primary" label="Chưa đọc" />}
                  </Stack>
                  <Typography display="block" variant="caption" color="text.secondary">
                    {statuses[conversation.status]} · {aiStatuses[conversation.ai_status]}
                  </Typography>
                  <Typography display="block" variant="caption" color="text.secondary">{localTime(conversation.last_message_at)}</Typography>
                </Box>
              </ListItemButton>)}
            </List>
            {result.meta.total > result.meta.limit && <Pagination size="small" aria-label="Phân trang hội thoại"
              count={Math.ceil(result.meta.total / result.meta.limit)} page={page} onChange={(_, next) => setPage(next)} />}
          </>}
        </Stack>
      </Paper>
      {selected ? <Chat key={selected} id={selected} back={() => setParams({})} />
        : <Paper variant="outlined" sx={{ p: 3, display: { xs: 'none', lg: 'block' } }}>
        <Typography color="text.secondary">Chọn một hội thoại để xem tin nhắn.</Typography>
      </Paper>}
    </Box>
  </Stack>;
}
