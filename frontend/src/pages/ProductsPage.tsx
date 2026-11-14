import { useState } from 'react';
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider, MenuItem, Pagination,
  Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { InboxQueryState } from '../components/InboxQueryState';
import { ProductForm, VariantForm } from '../components/ProductForms';
import { api } from '../services/api';
import { getProduct, listProducts, money, productError, statusLabels, type Variant } from '../services/products';

export function ProductsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [lowStock, setLowStock] = useState('');
  const navigate = useNavigate();
  const products = useQuery({
    queryKey: ['products', page, search, status, lowStock],
    queryFn: ({ signal }) => listProducts(signal, {
      page, limit: 10, search: search.trim() || undefined, status: status || undefined, low_stock: lowStock ? true : undefined,
    }),
  });
  const result = products.data;
  return <Stack spacing={2}>
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }} justifyContent="space-between">
      <Typography component="h1" variant="h4">Sản phẩm</Typography>
      <Button variant="contained" component={Link} to="/products/new">Thêm sản phẩm</Button>
    </Stack>
    <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '1.5fr 1fr 1fr' } }}>
      <TextField label="Tìm theo tên" value={search} inputProps={{ maxLength: 200 }}
        onChange={(event) => { setSearch(event.target.value); setPage(1); }} />
      <TextField label="Trạng thái" select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
        <MenuItem value="">Tất cả trạng thái</MenuItem>
        {Object.entries(statusLabels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
      </TextField>
      <TextField label="Tồn kho" select value={lowStock} onChange={(event) => { setLowStock(event.target.value); setPage(1); }}>
        <MenuItem value="">Tất cả tồn kho</MenuItem>
        <MenuItem value="low">Sắp hết / Hết hàng</MenuItem>
      </TextField>
    </Box>
    <InboxQueryState pending={products.isPending} error={products.isError} retry={() => void products.refetch()} />
    {result && !products.isError && (result.data.length ? <>
      <TableContainer component={Paper} variant="outlined">
        <Table aria-label="Danh sách sản phẩm" sx={{ minWidth: 610 }}>
          <TableHead><TableRow>
            <TableCell>Sản phẩm</TableCell><TableCell align="right">Biến thể</TableCell><TableCell align="right">Tồn kho</TableCell>
            <TableCell>Trạng thái</TableCell><TableCell>Hành động</TableCell>
          </TableRow></TableHead>
          <TableBody>
            {result.data.map((product) => {
              const out = product.variants.some((variant) => variant.stock === 0);
              const low = product.variants.some((variant) => variant.stock <= variant.low_stock_threshold);
              return <TableRow key={product.id}>
                <TableCell>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    {product.image_url && <Box component="img" src={product.image_url} alt="" loading="lazy"
                      sx={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 1 }} />}
                    <Typography fontWeight={700} sx={{ overflowWrap: 'anywhere' }}>{product.name}</Typography>
                  </Stack>
                </TableCell>
                <TableCell align="right">{product.variants.length}</TableCell>
                <TableCell align="right">
                  <Stack spacing={0.5} alignItems="flex-end">
                    <Typography>{product.total_stock.toLocaleString('vi-VN')}</Typography>
                    {low && <Chip size="small" color={out ? 'error' : 'warning'} label={out ? 'Hết hàng' : 'Sắp hết'} />}
                  </Stack>
                </TableCell>
                <TableCell><Chip size="small" color={product.status === 'ACTIVE' ? 'success' : 'default'} label={statusLabels[product.status]} /></TableCell>
                <TableCell><Button onClick={() => navigate('/products/' + product.id)} aria-label={'Mở ' + product.name}>Chi tiết</Button></TableCell>
              </TableRow>;
            })}
          </TableBody>
        </Table>
      </TableContainer>
      {result.meta.total > result.meta.limit && <Pagination count={Math.ceil(result.meta.total / result.meta.limit)}
        aria-label="Phân trang sản phẩm" page={page} onChange={(_, value) => setPage(value)} />}
    </> : <Typography color="text.secondary">
      {search || status || lowStock ? 'Không có sản phẩm nào khớp bộ lọc.' : 'Chưa có sản phẩm. Nhấn Thêm sản phẩm để bắt đầu.'}
    </Typography>)}
  </Stack>;
}

export function NewProductPage() {
  const navigate = useNavigate();
  return <Stack spacing={2} maxWidth={700}>
    <Button component={Link} to="/products" sx={{ alignSelf: 'flex-start' }}>Về sản phẩm</Button>
    <Typography component="h1" variant="h4">Thêm sản phẩm</Typography>
    <Paper variant="outlined" sx={{ p: 2 }}><ProductForm saved={(product) => navigate('/products/' + product.id, { replace: true })} /></Paper>
  </Stack>;
}

export function ProductDetailPage() {
  const id = useParams().id ?? '';
  const client = useQueryClient();
  const navigate = useNavigate();
  const [editProduct, setEditProduct] = useState(false);
  const [editVariant, setEditVariant] = useState<Variant | 'new' | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Variant | 'product' | null>(null);
  const query = useQuery({ queryKey: ['product', id], queryFn: ({ signal }) => getProduct(id, signal) });
  const product = query.data;
  const remove = useMutation({
    mutationFn: (target: Variant | 'product') => api.delete('/products/' + id + (target === 'product' ? '' : '/variants/' + target.id)),
    onSuccess: async (_, target) => {
      setDeleteTarget(null);
      if (target === 'product') {
        client.removeQueries({ queryKey: ['product', id] });
        navigate('/products', { replace: true });
      } else {
        await client.invalidateQueries({ queryKey: ['product', id] });
      }
      await client.invalidateQueries({ queryKey: ['products'] });
    },
  });
  function askDelete(target: Variant | 'product') {
    remove.reset();
    setDeleteTarget(target);
  }

  return <Stack spacing={2}>
    <Button component={Link} to="/products" sx={{ alignSelf: 'flex-start' }}>Về sản phẩm</Button>
    <InboxQueryState pending={query.isPending} error={query.isError} retry={() => void query.refetch()} />
    {product && !query.isError && <>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'flex-start' }}>
        {product.image_url && <Box component="img" src={product.image_url} alt={'Ảnh ' + product.name}
          sx={{ width: 132, height: 132, objectFit: 'cover', borderRadius: 2 }} />}
        <Stack spacing={1} sx={{ minWidth: 0 }}>
          <Typography component="h1" variant="h4" sx={{ overflowWrap: 'anywhere' }}>{product.name}</Typography>
          <Stack direction="row" flexWrap="wrap" gap={1}>
            <Chip label={statusLabels[product.status]} size="small" color={product.status === 'ACTIVE' ? 'success' : 'default'} />
            <Chip label={'Tổng tồn kho ' + product.total_stock.toLocaleString('vi-VN')} size="small" />
          </Stack>
          {product.description && <Typography sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{product.description}</Typography>}
          <Stack direction="row" gap={1} flexWrap="wrap">
            <Button variant="outlined" onClick={() => setEditProduct(true)}>Sửa sản phẩm</Button>
            <Button color="error" onClick={() => askDelete('product')}>Xóa sản phẩm</Button>
          </Stack>
        </Stack>
      </Stack>
      <Divider />
      <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center" justifyContent="space-between">
        <Typography component="h2" variant="h6">Biến thể</Typography>
        <Button variant="contained" onClick={() => setEditVariant('new')}>Thêm biến thể</Button>
      </Stack>
      {!product.variants.length && <Typography color="text.secondary">Chưa có biến thể. Thêm biến thể để mở bán.</Typography>}
      {product.variants.map((variant) => <Paper key={variant.id} variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} justifyContent="space-between">
          <Stack spacing={0.5} sx={{ minWidth: 0 }}>
            <Typography fontWeight={700} sx={{ overflowWrap: 'anywhere' }}>{variant.name}</Typography>
            <Typography>{money.format(variant.price)} · Tồn kho {variant.stock.toLocaleString('vi-VN')}</Typography>
            <Typography variant="body2" color="text.secondary">Ngưỡng sắp hết {variant.low_stock_threshold.toLocaleString('vi-VN')}</Typography>
          </Stack>
          <Stack direction="row" alignItems="center">
            <Button aria-label={'Sửa ' + variant.name} onClick={() => setEditVariant(variant)}>Sửa</Button>
            <Button color="error" aria-label={'Xóa ' + variant.name} onClick={() => askDelete(variant)}>Xóa</Button>
          </Stack>
        </Stack>
      </Paper>)}
      <Dialog open={editProduct} onClose={() => setEditProduct(false)} fullWidth maxWidth="sm" aria-labelledby="edit-product-title">
        <DialogTitle id="edit-product-title">Sửa sản phẩm</DialogTitle>
        <DialogContent dividers>{editProduct && <ProductForm product={product} saved={() => setEditProduct(false)} />}</DialogContent>
        <DialogActions><Button onClick={() => setEditProduct(false)}>Đóng</Button></DialogActions>
      </Dialog>
      <Dialog open={editVariant !== null} onClose={() => setEditVariant(null)} fullWidth maxWidth="sm" aria-labelledby="edit-variant-title">
        <DialogTitle id="edit-variant-title">{editVariant === 'new' ? 'Thêm biến thể' : 'Sửa biến thể'}</DialogTitle>
        <DialogContent dividers>{editVariant && <VariantForm productId={id}
          variant={editVariant === 'new' ? undefined : editVariant} saved={() => setEditVariant(null)} />}</DialogContent>
        <DialogActions><Button onClick={() => setEditVariant(null)}>Đóng</Button></DialogActions>
      </Dialog>
      <Dialog open={deleteTarget !== null} onClose={() => { if (!remove.isPending) setDeleteTarget(null); }}
        aria-labelledby="delete-product-title">
        <DialogTitle id="delete-product-title">{deleteTarget === 'product' ? 'Xóa sản phẩm' : 'Xóa biến thể'}</DialogTitle>
        <DialogContent>
          <Typography sx={{ overflowWrap: 'anywhere' }}>
            {deleteTarget === 'product'
              ? 'Xóa ' + product.name + '? Sản phẩm và biến thể sẽ bị ẩn khỏi danh mục. Đơn hàng cũ vẫn được giữ.'
              : 'Xóa ' + (deleteTarget?.name ?? '') + '?' + (product.variants.length === 1 ? ' Đây là biến thể cuối. Sản phẩm sẽ chuyển sang ngừng bán.' : '')}
          </Typography>
          {remove.isError && <Alert severity="error" sx={{ mt: 1 }}>{productError(remove.error, 'Chưa xóa được. Vui lòng thử lại.')}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button disabled={remove.isPending} onClick={() => setDeleteTarget(null)}>Hủy</Button>
          <Button color="error" variant="contained" disabled={remove.isPending} onClick={() => { if (deleteTarget) remove.mutate(deleteTarget); }}>
            {remove.isPending ? 'Đang xóa…' : 'Xác nhận xóa'}
          </Button>
        </DialogActions>
      </Dialog>
    </>}
  </Stack>;
}
