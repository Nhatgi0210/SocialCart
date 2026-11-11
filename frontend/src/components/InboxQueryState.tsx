import { Alert, Button, Skeleton, Stack } from '@mui/material';

export function InboxQueryState({ pending, error, retry }: { pending: boolean; error: boolean; retry: () => void }) {
  if (pending) return <Stack role="status" aria-label="Đang tải dữ liệu">
    <Skeleton animation={false} /><Skeleton animation={false} /><Skeleton animation={false} />
  </Stack>;
  if (error) return <Alert severity="error" action={<Button color="inherit" onClick={retry}>Thử lại</Button>}>
    Chưa tải được dữ liệu.
  </Alert>;
  return null;
}
