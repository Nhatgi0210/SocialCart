import { useState } from 'react';
import { Alert, Box, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Result } from '../services/inbox';
import {
  imageTypes, maxImageBytes, productError, uploadProductImage,
  type Product, type ProductStatus, type Variant, type VariantInput,
} from '../services/products';

const emptyVariant = (): VariantInput => ({ name: '', price: 1, stock: 0, low_stock_threshold: 0 });

function VariantFields({ draft, change, disabled }: {
  draft: VariantInput; change: (next: VariantInput) => void; disabled: boolean;
}) {
  return <Stack spacing={1.5}>
    <TextField label="Tên biến thể" value={draft.name} required disabled={disabled}
      inputProps={{ maxLength: 100 }} onChange={(event) => change({ ...draft, name: event.target.value })} />
    <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, minmax(0, 1fr))' } }}>
      <TextField label="Giá (VNĐ)" type="number" required disabled={disabled} value={Number.isNaN(draft.price) ? '' : draft.price}
        inputProps={{ min: 1, max: 2147483647, step: 1 }}
        onChange={(event) => change({ ...draft, price: event.target.value === '' ? NaN : Number(event.target.value) })} />
      <TextField label="Tồn kho" type="number" required disabled={disabled} value={Number.isNaN(draft.stock) ? '' : draft.stock}
        inputProps={{ min: 0, max: 2147483647, step: 1 }}
        onChange={(event) => change({ ...draft, stock: event.target.value === '' ? NaN : Number(event.target.value) })} />
      <TextField label="Ngưỡng sắp hết" type="number" required disabled={disabled}
        value={Number.isNaN(draft.low_stock_threshold) ? '' : draft.low_stock_threshold}
        inputProps={{ min: 0, max: 2147483647, step: 1 }}
        onChange={(event) => change({ ...draft, low_stock_threshold: event.target.value === '' ? NaN : Number(event.target.value) })} />
    </Box>
  </Stack>;
}

export function ProductForm({ product, saved }: { product?: Product; saved: (product: Product) => void }) {
  const client = useQueryClient();
  const [name, setName] = useState(product?.name ?? '');
  const [description, setDescription] = useState(product?.description ?? '');
  const [status, setStatus] = useState<ProductStatus>(product?.status ?? 'ACTIVE');
  const [imageUrl, setImageUrl] = useState(product?.image_url ?? null);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const [variants, setVariants] = useState([{ key: 0, draft: emptyVariant() }]);
  const save = useMutation({
    mutationFn: async () => {
      const url = file ? await uploadProductImage(file) : imageUrl;
      if (file) {
        setImageUrl(url);
        setFile(null);
      }
      const fields = { name: name.trim(), description: description.trim() };
      const result = product
        ? await api.put<Result<Product>>('/products/' + product.id, { ...fields, status, image_url: url })
        : await api.post<Result<Product>>('/products', {
          ...fields, ...(url ? { image_url: url } : {}), variants: variants.map(({ draft }) => ({ ...draft, name: draft.name.trim() })),
        });
      return result.data.data;
    },
    onSuccess: (updated) => {
      client.setQueryData(['product', updated.id], updated);
      void client.invalidateQueries({ queryKey: ['products'] });
      saved(updated);
    },
  });

  return <Stack component="form" spacing={2} onSubmit={(event) => {
    event.preventDefault();
    if (name.trim() && !fileError && !save.isPending && (product || variants.every(({ draft }) => draft.name.trim()))) save.mutate();
  }}>
    <TextField label="Tên sản phẩm" required disabled={save.isPending} value={name}
      inputProps={{ maxLength: 200 }} onChange={(event) => setName(event.target.value)} />
    <TextField label="Mô tả" multiline minRows={2} disabled={save.isPending} value={description}
      inputProps={{ maxLength: 5000 }} onChange={(event) => setDescription(event.target.value)} />
    {product && <TextField label="Trạng thái" select disabled={save.isPending} value={status}
      onChange={(event) => setStatus(event.target.value as ProductStatus)}>
      <MenuItem value="ACTIVE" disabled={!product.variants.length}>Đang bán</MenuItem>
      <MenuItem value="INACTIVE">Ngừng bán</MenuItem>
    </TextField>}
    <Stack spacing={1}>
      {imageUrl && <Box component="img" src={imageUrl} alt="Ảnh sản phẩm" sx={{ width: 112, height: 112, objectFit: 'cover', borderRadius: 2 }} />}
      <Stack spacing={1} direction={{ xs: 'column', sm: 'row' }}>
        <Button component="label" variant="outlined" disabled={save.isPending}>
          Chọn ảnh
          <input type="file" aria-label="Ảnh sản phẩm" accept={imageTypes.join(',')} hidden
            disabled={save.isPending} onChange={(event) => {
              const next = event.target.files?.[0];
              event.target.value = '';
              if (!next) return;
              if (!imageTypes.includes(next.type) || next.size > maxImageBytes) {
                setFileError('Chọn ảnh JPEG, PNG hoặc WebP tối đa 5 MiB.');
                return;
              }
              setFileError('');
              setFile(next);
            }} />
        </Button>
        {(file || imageUrl || fileError) && <Button disabled={save.isPending}
          onClick={() => { setImageUrl(null); setFile(null); setFileError(''); }}>Bỏ ảnh</Button>}
      </Stack>
      {file && <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{file.name}</Typography>}
      {fileError && <Alert severity="error">{fileError}</Alert>}
    </Stack>
    {!product && <>
      <Typography component="h2" variant="h6">Biến thể</Typography>
      {variants.map(({ key, draft }, index) => <Paper key={key} variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={1.5}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography fontWeight={700}>Biến thể {index + 1}</Typography>
            {variants.length > 1 && <Button disabled={save.isPending} color="error"
              onClick={() => setVariants((rows) => rows.filter((row) => row.key !== key))}>Bỏ biến thể</Button>}
          </Stack>
          <VariantFields draft={draft} disabled={save.isPending} change={(next) =>
            setVariants((rows) => rows.map((row) => row.key === key ? { key, draft: next } : row))} />
        </Stack>
      </Paper>)}
      <Button variant="outlined" disabled={save.isPending} onClick={() =>
        setVariants((rows) => [...rows, { key: rows[rows.length - 1].key + 1, draft: emptyVariant() }])}>Thêm biến thể</Button>
    </>}
    {save.isError && <Alert severity="error">{productError(save.error, 'Chưa lưu được sản phẩm. Vui lòng thử lại.')}</Alert>}
    <Button type="submit" variant="contained" disabled={save.isPending || !name.trim() || !!fileError
      || (!product && variants.some(({ draft }) => !draft.name.trim()))}>
      {save.isPending ? 'Đang lưu…' : product ? 'Lưu thông tin' : 'Tạo sản phẩm'}
    </Button>
  </Stack>;
}

export function VariantForm({ productId, variant, saved }: {
  productId: string; variant?: Variant; saved: () => void;
}) {
  const client = useQueryClient();
  const [draft, setDraft] = useState<VariantInput>(variant ?? emptyVariant());
  // Keep the version attached to this draft even if a background query refreshes.
  const [version] = useState(variant?.version);
  const save = useMutation({
    mutationFn: async () => {
      const path = '/products/' + productId + '/variants';
      const body = { name: draft.name.trim(), price: draft.price, stock: draft.stock, low_stock_threshold: draft.low_stock_threshold };
      if (variant) {
        await api.put(path + '/' + variant.id, { ...body, expected_version: version });
      } else {
        await api.post(path, body);
      }
    },
    onSuccess: async () => {
      await Promise.all([client.invalidateQueries({ queryKey: ['product', productId] }),
        client.invalidateQueries({ queryKey: ['products'] })]);
      saved();
    },
  });
  return <Stack component="form" spacing={2} onSubmit={(event) => {
    event.preventDefault();
    if (draft.name.trim() && !save.isPending) save.mutate();
  }}>
    <VariantFields draft={draft} change={setDraft} disabled={save.isPending} />
    {save.isError && <Alert severity="error">{productError(save.error, 'Chưa lưu được biến thể. Vui lòng thử lại.')}</Alert>}
    <Button type="submit" variant="contained" disabled={save.isPending || !draft.name.trim()}>
      {save.isPending ? 'Đang lưu…' : 'Lưu biến thể'}
    </Button>
  </Stack>;
}
