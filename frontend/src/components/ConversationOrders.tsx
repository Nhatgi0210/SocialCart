import { useState } from 'react';
import { Button, Link, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { inboxGet, type Conversation, type PageResult } from '../services/inbox';
import { orderStatuses, type Order } from '../services/orders';
import { InboxQueryState } from './InboxQueryState';
import { OrderForm } from './OrderForm';

export function ConversationOrders({ conversation }: { conversation: Conversation }) {
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const orders = useQuery({
    queryKey: ['orders', 'conversation', conversation.id],
    queryFn: ({ signal }) => inboxGet<PageResult<Order>>('/orders', signal, { conversation_id: conversation.id, limit: 5 }),
  });
  return <Stack spacing={1}>
    <Typography component="h3" fontWeight={700}>Đơn của hội thoại</Typography>
    <Button size="small" variant="outlined" onClick={() => setCreating(true)}>Tạo đơn hàng thủ công</Button>
    <InboxQueryState pending={orders.isPending} error={orders.isError} retry={() => void orders.refetch()} />
    {orders.data?.data.length === 0 && <Typography variant="body2" color="text.secondary">Chưa có đơn.</Typography>}
    {orders.data?.data.map((order) => <Link key={order.id} component={RouterLink} to={'/orders/' + order.id}
      sx={{ overflowWrap: 'anywhere' }}>{order.order_code} · {orderStatuses[order.status]}</Link>)}
    {(orders.data?.meta.total ?? 0) > 5 && <Link component={RouterLink}
      to={'/orders?conversation=' + conversation.id}>Xem tất cả đơn của hội thoại</Link>}
    {creating && <OrderForm conversation={conversation} onClose={() => setCreating(false)}
      onSaved={(order) => navigate('/orders/' + order.id)} />}
  </Stack>;
}
