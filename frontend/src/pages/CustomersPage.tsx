import { useState } from 'react';
import { Button, Chip, List, ListItemButton, ListItemText, MenuItem, Pagination, Stack, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { CustomerProfile } from '../components/CustomerProfile';
import { InboxQueryState } from '../components/InboxQueryState';
import { inboxGet, platforms, type Customer, type PageResult } from '../services/inbox';

export function CustomersPage() {
  const [page, setPage] = useState(1);
  const [platform, setPlatform] = useState('');
  const [search, setSearch] = useState('');
  const query = useQuery({
    queryKey: ['customers', page, platform, search],
    queryFn: ({ signal }) => inboxGet<PageResult<Customer>>('/customers', signal, {
      page, limit: 10, platform: platform || undefined, search: search.trim() || undefined,
    }),
  });
  const result = query.data;
  return <Stack spacing={2}>
    <Typography component="h1" variant="h4">Khách hàng</Typography>
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
      <TextField label="Tìm theo tên" value={search} inputProps={{ maxLength: 100 }}
        onChange={(event) => { setSearch(event.target.value); setPage(1); }} />
      <TextField select label="Nền tảng" value={platform} sx={{ minWidth: 180 }}
        onChange={(event) => { setPlatform(event.target.value); setPage(1); }}>
        <MenuItem value="">Tất cả nền tảng</MenuItem>
        {Object.entries(platforms).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
      </TextField>
    </Stack>
    <InboxQueryState pending={query.isPending} error={query.isError} retry={() => void query.refetch()} />
    {result && !query.isError && <>
      {result.data.length === 0 && <Typography color="text.secondary">Không tìm thấy khách hàng.</Typography>}
      <List disablePadding aria-label="Danh sách khách hàng">
        {result.data.map((customer) => <ListItemButton key={customer.id} component={Link} to={'/customers/' + customer.id}
          sx={{ gap: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
          <ListItemText primary={customer.name} sx={{ overflowWrap: 'anywhere' }} />
          <Chip label={platforms[customer.platform]} size="small" />
        </ListItemButton>)}
      </List>
      {result.meta.total > result.meta.limit && <Pagination aria-label="Phân trang khách hàng"
        count={Math.ceil(result.meta.total / result.meta.limit)} page={page} onChange={(_, next) => setPage(next)} />}
    </>}
  </Stack>;
}

export function CustomerDetailPage() {
  const { id } = useParams();
  return <Stack spacing={2}>
    <Button component={Link} to="/customers" sx={{ alignSelf: 'flex-start' }}>Về danh sách khách hàng</Button>
    <Typography component="h1" variant="h4">Hồ sơ khách hàng</Typography>
    {id && <CustomerProfile key={id} id={id} />}
  </Stack>;
}
