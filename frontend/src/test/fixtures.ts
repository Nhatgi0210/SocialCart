import type { TokenData } from '../types/auth';

export const tokenData: TokenData = {
  access_token: 'local-test-access-token',
  token_type: 'bearer',
  expires_in: 900,
  user: { id: '550e8400-e29b-41d4-a716-000000000001', email: 'seller@example.test', name: 'Chủ shop thử nghiệm' },
};
