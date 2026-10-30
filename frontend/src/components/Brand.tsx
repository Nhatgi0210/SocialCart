import ShoppingBagOutlined from '@mui/icons-material/ShoppingBagOutlined';
import { Box, Stack, Typography } from '@mui/material';

export function Brand() {
  return <Stack direction="row" alignItems="center" spacing={1.25}>
    <Box sx={{ bgcolor: 'primary.dark', color: 'white', p: 1, borderRadius: 2, display: 'flex' }}>
      <ShoppingBagOutlined aria-hidden="true" />
    </Box>
    <Typography fontWeight={700} fontSize={23} letterSpacing="-0.7px">SocialCart</Typography>
  </Stack>;
}
