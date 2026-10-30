import { Paper, Stack, Typography } from '@mui/material';
import InboxOutlined from '@mui/icons-material/InboxOutlined';

export function WorkspacePage({ title }: { title: string }) {
  return <Stack spacing={3}>
    <Typography component="h1" variant="h1">{title}</Typography>
    <Paper variant="outlined" sx={{ p: { xs: 4, md: 7 }, textAlign: 'center' }}>
      <InboxOutlined sx={{ fontSize: 40, color: 'primary.dark', mb: 2 }} />
      <Typography component="h2" variant="h2" mb={1}>Không gian làm việc đang được chuẩn bị</Typography>
      <Typography color="text.secondary">Tính năng này sẽ sớm có mặt tại đây.</Typography>
    </Paper>
  </Stack>;
}
