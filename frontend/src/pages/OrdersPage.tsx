import { useState } from 'react';
import {
  Alert, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider, MenuItem, Pagination,
  Paper, Stack, TextField, Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { InboxQueryState } from '../components/InboxQueryState';
import { OrderForm } from '../components/OrderForm';
import { inboxGet, localTime, type PageResult, type Result } from '../services/inbox';
import { orderStatuses, refreshOrderQueries, useOrderWrite, type Order, type OrderStatus } from '../services/orders';
import { money, productError } from '../services/products';

const actions = {
  CONFIRMED: { label: 'Xác nhận đơn', description: 'Xác nhận đơn và trừ số lượng đã đặt khỏi tồn kho.' },
  SHIPPING: { label: 'Chuyển sang đang giao', description: 'Đánh dấu đơn đang giao.' },
  COMPLETED: { label: 'Hoàn thành đơn', description: 'Đánh dấu đơn đã giao xong.' },
  CANCELLED: { label: 'Hủy đơn', description: 'Hủy đơn. Số lượng đã trừ sẽ được hoàn lại nếu đơn đã xác nhận hoặc đang giao.' },
};
type Action = keyof typeof actions;
const available: Record<OrderStatus, Action[]> = {
  PENDING: ['CONFIRMED', 'CANCELLED'], CONFIRMED: ['SHIPPING', 'CANCELLED'],
  SHIPPING: ['COMPLETED', 'CANCELLED'], COMPLETED: [], CANCELLED: [],
};

export function OrdersPage() {
  const [params] = useSearchParams();
  const conversationId = params.get('conversation');
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<OrderStatus | ''>('');
  const query = useQuery({
    queryKey: ['orders', 'list', conversationId, status, page],
    queryFn: ({ signal }) => inboxGet<PageResult<Order>>('/orders', signal, {
      conversation_id: conversationId ?? undefined, status: status || undefined, page,
    }),
  });
  return <Stack spacing={2}>
    <Typography component="h1" variant="h4">Đơn hàng</Typography>
    {conversationId && <Stack direction="row" gap={1} flexWrap="wrap">
      <Button component={Link} to={'/inbox?conversation=' + conversationId}>Về hội thoại</Button>
      <Button component={Link} to="/orders" onClick={() => setPage(1)}>Xem tất cả đơn</Button>
    </Stack>}
    <TextField select size="small" label="Trạng thái đơn" value={status} sx={{ maxWidth: 260 }}
      onChange={(event) => { setStatus(event.target.value as OrderStatus | ''); setPage(1); }}>
      <MenuItem value="">Tất cả trạng thái</MenuItem>
      {Object.entries(orderStatuses).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
    </TextField>
    <InboxQueryState pending={query.isPending} error={query.isError} retry={() => void query.refetch()} />
    {query.data && !query.isError && <>
      {query.data.data.length === 0 && <Typography color="text.secondary">Không có đơn hàng trong danh sách này.</Typography>}
      {query.data.data.map((order) => <Paper key={order.id} variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }} justifyContent="space-between">
          <Stack spacing={0.5} minWidth={0}>
            <Typography fontWeight={700}>{order.customer_name ?? 'Đơn hàng'}</Typography>
            <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{order.order_code} · {localTime(order.created_at)}</Typography>
          </Stack>
          <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center">
            <Chip size="small" label={orderStatuses[order.status]} />
            <Typography fontWeight={700}>{money.format(order.total_amount)}</Typography>
            <Button component={Link} to={'/orders/' + order.id}>Chi tiết</Button>
          </Stack>
        </Stack>
      </Paper>)}
      {query.data.meta.total > query.data.meta.limit && <Pagination aria-label="Phân trang đơn hàng" page={page}
        count={Math.ceil(query.data.meta.total / query.data.meta.limit)} onChange={(_, next) => setPage(next)} />}
    </>}
  </Stack>;
}

export function OrderDetailPage() {
  const id = useParams().id ?? '';
  const client = useQueryClient();
  const [editing, setEditing] = useState<Order | null>(null);
  const [action, setAction] = useState<{ status: Action; expected_version: number } | null>(null);
  const query = useQuery({
    queryKey: ['order', id],
    queryFn: ({ signal }) => inboxGet<Result<Order>>('/orders/' + id, signal),
  });
  const write = useOrderWrite('patch', '/orders/' + id + '/status');
  const transition = useMutation({
    mutationFn: write,
    onSuccess: (saved) => {
      setAction(null);
      refreshOrderQueries(client, saved);
    },
    onError: () => void query.refetch(),
  });
  const order = query.data?.data;
  return <Stack spacing={2}>
    <Button component={Link} to="/orders" sx={{ alignSelf: 'flex-start' }}>Về danh sách đơn</Button>
    <Typography component="h1" variant="h4">Chi tiết đơn hàng</Typography>
    <InboxQueryState pending={query.isPending} error={query.isError} retry={() => void query.refetch()} />
    {order && !query.isError && <>
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={1}>
          <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center">
            <Typography component="h2" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{order.order_code}</Typography>
            <Chip label={orderStatuses[order.status]} />
          </Stack>
          <Typography variant="body2" color="text.secondary">
            {localTime(order.created_at)} · {order.created_by === 'AI' ? 'AI' : 'Người bán'}
          </Typography>
          <Typography sx={{ overflowWrap: 'anywhere' }}>{order.customer_name} · {order.phone_number}</Typography>
          <Typography sx={{ overflowWrap: 'anywhere' }}>{order.address}</Typography>
          {order.note && <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{order.note}</Typography>}
          {order.conversation_id && <Button component={Link} to={'/inbox?conversation=' + order.conversation_id}
            sx={{ alignSelf: 'flex-start' }}>Về hội thoại gốc</Button>}
          <Divider />
          {order.items.map((item) => <Stack key={item.id} direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={1}>
            <Typography sx={{ overflowWrap: 'anywhere' }}>{item.product_name} · {item.variant_name}</Typography>
            <Typography>{item.quantity} × {money.format(item.unit_price)} = {money.format(item.subtotal)}</Typography>
          </Stack>)}
          <Typography fontWeight={700}>Tổng tiền {money.format(order.total_amount)}</Typography>
        </Stack>
      </Paper>
      <Stack direction="row" flexWrap="wrap" gap={1}>
        {order.status === 'PENDING' && <Button variant="outlined" onClick={() => setEditing(order)}>Sửa đơn chờ</Button>}
        {available[order.status].map((status) => <Button key={status} variant={status === 'CANCELLED' ? 'outlined' : 'contained'}
          color={status === 'CANCELLED' ? 'error' : 'primary'} onClick={() => {
            transition.reset();
            setAction({ status, expected_version: order.version });
          }}>{actions[status].label}</Button>)}
      </Stack>
    </>}
    {editing && <OrderForm order={editing} onClose={() => setEditing(null)} onSaved={() => setEditing(null)} />}
    {action && <Dialog open onClose={transition.isPending ? undefined : () => setAction(null)} aria-labelledby="order-status-title">
      <DialogTitle id="order-status-title">{actions[action.status].label}</DialogTitle>
      <DialogContent>
        <Typography>{actions[action.status].description}</Typography>
        {transition.isError && <Alert sx={{ mt: 1 }} severity="error">
          {productError(transition.error, 'Chưa cập nhật được đơn. Vui lòng thử lại.')}
        </Alert>}
      </DialogContent>
      <DialogActions>
        <Button disabled={transition.isPending} onClick={() => setAction(null)}>Đóng</Button>
        <Button variant="contained" color={action.status === 'CANCELLED' ? 'error' : 'primary'}
          disabled={transition.isPending} onClick={() => transition.mutate(action)}>Thực hiện</Button>
      </DialogActions>
    </Dialog>}
  </Stack>;
}
