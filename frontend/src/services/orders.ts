import { useRef } from 'react';
import type { QueryClient } from '@tanstack/react-query';
import { api } from './api';
import type { Result } from './inbox';

export const orderStatuses = {
  PENDING: 'Chờ xác nhận', CONFIRMED: 'Đã xác nhận', SHIPPING: 'Đang giao',
  COMPLETED: 'Hoàn thành', CANCELLED: 'Đã hủy',
};
export type OrderStatus = keyof typeof orderStatuses;
export type OrderItem = {
  id: string; variant_id: string; product_name: string; variant_name: string;
  quantity: number; unit_price: number; subtotal: number;
};
export type Order = {
  id: string; order_code: string; customer_id: string; conversation_id: string | null;
  customer_name: string | null; phone_number: string | null; address: string | null; note: string;
  status: OrderStatus; created_by: 'SELLER' | 'AI'; total_amount: number;
  version: number; created_at: string; updated_at: string; items: OrderItem[];
};

export function useOrderWrite(method: 'post' | 'patch', path: string) {
  const previous = useRef<{ request: string; key: string }>();
  return async (body: object) => {
    const request = JSON.stringify(body);
    if (previous.current?.request !== request) previous.current = { request, key: crypto.randomUUID() };
    const headers = { 'Idempotency-Key': previous.current.key };
    return (await api.request<Result<Order>>({ method, url: path, data: body, headers })).data.data;
  };
}

export function refreshOrderQueries(client: QueryClient, order: Order) {
  void client.cancelQueries({ queryKey: ['order', order.id], exact: true });
  client.setQueryData<Result<Order>>(['order', order.id], (cached) =>
    cached && cached.data.version > order.version ? cached : { success: true, data: order });
  for (const key of ['orders', 'customer', 'products', 'product']) {
    void client.invalidateQueries({ queryKey: [key] });
  }
}
