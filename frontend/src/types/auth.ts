export interface Seller {
  id: string;
  email: string;
  name: string;
}

export interface TokenData {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: Seller;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
}
