import { useState } from 'react';
import { Alert, Autocomplete, Button, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listProducts, money, productError } from '../services/products';
import { refreshOrderQueries, useOrderWrite, type Order } from '../services/orders';
import type { Conversation } from '../services/inbox';

type DraftItem = { id: string; label: string; price: number; quantity: number };
type FormProps = { onClose: () => void; onSaved: (order: Order) => void } &
  ({ order: Order; conversation?: never } | { conversation: Conversation; order?: never });

export function OrderForm({ order, conversation, onClose, onSaved }: FormProps) {
  const [name, setName] = useState(order?.customer_name ?? conversation?.customer.name ?? '');
  const [phone, setPhone] = useState(order?.phone_number ?? '');
  const [address, setAddress] = useState(order?.address ?? '');
  const [note, setNote] = useState(order?.note ?? '');
  const [items, setItems] = useState<DraftItem[]>(() => order?.items.map((item) => ({
    id: item.variant_id, label: item.product_name + ' · ' + item.variant_name, price: item.unit_price, quantity: item.quantity,
  })) ?? []);
  const [search, setSearch] = useState('');
  const client = useQueryClient();
  const title = order ? 'Sửa đơn chờ' : 'Tạo đơn hàng thủ công';
  const catalog = useQuery({
    queryKey: ['products', 'order-picker', search],
    queryFn: ({ signal }) => listProducts(signal, { status: 'ACTIVE', search: search.trim() || undefined }),
  });
  const choices = catalog.data?.data.flatMap((product) => product.variants.map((variant) => ({
    id: variant.id, name: product.name + ' · ' + variant.name,
    label: product.name + ' · ' + variant.name + ' · ' + money.format(variant.price) + ' · Tồn ' + variant.stock,
    price: variant.price, stock: variant.stock,
  }))) ?? [];
  const write = useOrderWrite(order ? 'patch' : 'post', order ? '/orders/' + order.id : '/orders');
  const save = useMutation({
    mutationFn: write,
    onSuccess: (saved) => {
      refreshOrderQueries(client, saved);
      onSaved(saved);
    },
  });
  const quantityValid = items.length > 0 && items.every((item) =>
    Number.isInteger(item.quantity) && item.quantity > 0 && item.quantity <= 1_000_000);
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return <Dialog open onClose={save.isPending ? undefined : onClose} fullWidth maxWidth="sm" aria-labelledby="order-form-title">
    <Stack component="form" onSubmit={(event) => {
      event.preventDefault();
      if (!quantityValid || !name.trim() || !/^[0-9]{10,11}$/.test(phone.trim()) || !address.trim() || save.isPending) return;
      const input = items.map((item) => ({ variant_id: item.id, quantity: item.quantity }));
      const fields = { customer_name: name.trim(), phone_number: phone.trim(), address: address.trim(), note };
      if (order) {
        const changedItems = items.length !== order.items.length || order.items.some((original) =>
          !input.some((item) => item.variant_id === original.variant_id && item.quantity === original.quantity));
        save.mutate({ ...fields, expected_version: order.version, ...(changedItems ? { items: input } : {}) });
      } else if (conversation) {
        save.mutate({ ...fields, conversation_id: conversation.id, customer_id: conversation.customer.id, items: input });
      }
    }}>
      <DialogTitle id="order-form-title">{title}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <TextField label="Người nhận" required value={name} disabled={save.isPending} inputProps={{ maxLength: 100 }}
            onChange={(event) => setName(event.target.value)} />
          <TextField label="Số điện thoại" type="tel" required value={phone} disabled={save.isPending}
            inputProps={{ maxLength: 11, pattern: '[0-9]{10,11}' }} onChange={(event) => setPhone(event.target.value)} />
          <TextField label="Địa chỉ giao hàng" required value={address} disabled={save.isPending} inputProps={{ maxLength: 500 }}
            onChange={(event) => setAddress(event.target.value)} />
          <TextField label="Ghi chú" multiline value={note} disabled={save.isPending} inputProps={{ maxLength: 5000 }}
            onChange={(event) => setNote(event.target.value)} />
          <Autocomplete options={choices} value={null} inputValue={search} loading={catalog.isFetching}
            disabled={save.isPending} onInputChange={(_, value) => setSearch(value)} filterOptions={(options) => options}
            getOptionLabel={(option) => option.label} getOptionKey={(option) => option.id}
            getOptionDisabled={(option) => option.stock === 0 || items.some((item) => item.id === option.id)}
            noOptionsText="Không tìm thấy biến thể" loadingText="Đang tải sản phẩm…"
            onChange={(_, choice) => {
              if (choice) {
                const original = order?.items.find((item) => item.variant_id === choice.id);
                const label = original ? original.product_name + ' · ' + original.variant_name : choice.name;
                setItems((rows) => [...rows, {
                  id: choice.id, label, price: original?.unit_price ?? choice.price, quantity: 1,
                }]);
              }
              setSearch('');
            }} renderInput={(params) => <TextField {...params} label="Tìm sản phẩm để thêm biến thể"
              inputProps={{ ...params.inputProps, maxLength: 200 }} />} />
          {catalog.isError && <Alert severity="error" action={<Button onClick={() => void catalog.refetch()}>Thử lại</Button>}>
            Chưa tải được sản phẩm.
          </Alert>}
          {items.map((item) => <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
              <Typography sx={{ flex: 1, overflowWrap: 'anywhere' }}>{item.label} · {money.format(item.price)}</Typography>
              <TextField label="Số lượng" size="small" type="number" required disabled={save.isPending}
                value={Number.isNaN(item.quantity) ? '' : item.quantity} sx={{ width: 110 }}
                inputProps={{ min: 1, max: 1000000, step: 1, 'aria-label': 'Số lượng ' + item.label }}
                onChange={(event) => setItems((rows) => rows.map((row) => row.id === item.id
                  ? { ...row, quantity: event.target.value === '' ? NaN : Number(event.target.value) } : row))} />
              <Button color="error" disabled={save.isPending} aria-label={'Bỏ ' + item.label}
                onClick={() => setItems((rows) => rows.filter((row) => row.id !== item.id))}>Bỏ</Button>
            </Stack>
          </Paper>)}
          <Typography fontWeight={700}>Tạm tính {money.format(Number.isFinite(total) ? total : 0)}</Typography>
          {save.isError && <Alert severity="error">{productError(save.error, 'Chưa lưu được đơn. Vui lòng thử lại.')}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button disabled={save.isPending} onClick={onClose}>Đóng</Button>
        <Button type="submit" variant="contained" disabled={save.isPending || !quantityValid}>
          {save.isPending ? 'Đang lưu…' : order ? 'Lưu thay đổi' : 'Tạo đơn chờ'}
        </Button>
      </DialogActions>
    </Stack>
  </Dialog>;
}
