import axios from 'axios';
import { api } from './api';
import type { PageResult, Result } from './inbox';

export type ProductStatus = 'ACTIVE' | 'INACTIVE';
export type VariantInput = { name: string; price: number; stock: number; low_stock_threshold: number };
export type Variant = VariantInput & { id: string; product_id: string; version: number };
export type Product = {
  id: string;
  name: string;
  description: string;
  image_url: string | null;
  status: ProductStatus;
  total_stock: number;
  variants: Variant[];
  created_at: string;
};
export async function listProducts(signal: AbortSignal, params: object) {
  return (await api.get<PageResult<Product>>('/products', { signal, params })).data;
}

export async function getProduct(id: string, signal: AbortSignal) {
  return (await api.get<Result<Product>>('/products/' + id, { signal })).data.data;
}

export async function uploadProductImage(file: File) {
  const data = new FormData();
  data.append('file', file);
  return (await api.post<Result<{ image_url: string }>>('/products/images', data)).data.data.image_url;
}

export function productError(error: unknown, fallback: string) {
  return axios.isAxiosError(error) ? (error.response?.data?.error?.message ?? fallback) : fallback;
}

export const statusLabels = { ACTIVE: 'Đang bán', INACTIVE: 'Ngừng bán' };
export const money = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });
export const imageTypes = ['image/jpeg', 'image/png', 'image/webp'];
export const maxImageBytes = 5 * 1024 * 1024;
