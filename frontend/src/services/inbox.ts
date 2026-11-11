import { api } from './api';

export type Platform = 'FACEBOOK' | 'ZALO';
export type Status = 'NEW' | 'IN_PROGRESS' | 'RESOLVED';
export type AIStatus = 'AI_HANDLING' | 'NEEDS_SELLER' | 'SELLER_HANDLING';
export interface Customer {
  id: string;
  name: string;
  platform: Platform;
  platform_user_id: string;
  platform_account_id: string;
  created_at: string;
}
export interface Note { id: string; customer_id: string; content: string; created_at: string }
export interface CustomerDetail {
  customer: Customer;
  notes: Note[];
  conversation_ids: string[];
  order_ids: string[];
}
export interface Conversation {
  id: string;
  customer: Customer;
  platform: Platform;
  status: Status;
  ai_status: AIStatus;
  is_read: boolean;
  version: number;
  last_message_at: string;
  last_message_preview: string;
  created_at: string;
}
export interface Message {
  id: string;
  content: string;
  sender: 'CUSTOMER' | 'AI' | 'SELLER';
  status: 'SENDING' | 'SENT' | 'FAILED';
  delivery_unknown: boolean;
  created_at: string;
}
export interface Result<T> { success: true; data: T }
export interface PageResult<T> extends Result<T[]> {
  meta: { page: number; limit: number; total: number };
}

export async function inboxGet<T>(path: string, signal: AbortSignal, params?: object) {
  return (await api.get<T>(path, { signal, params })).data;
}

export const platforms = { FACEBOOK: 'Facebook', ZALO: 'Zalo OA' };
export const statuses = { NEW: 'Mới', IN_PROGRESS: 'Đang xử lý', RESOLVED: 'Đã xử lý' };
export const aiStatuses = { AI_HANDLING: 'AI đang xử lý', NEEDS_SELLER: 'Cần người bán', SELLER_HANDLING: 'Người bán đang xử lý' };
const date = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' });
export const localTime = (iso: string) => date.format(new Date(iso));
