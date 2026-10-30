import axios, { AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';
import { useSession } from '../stores/session';
import type { ApiSuccess, TokenData } from '../types/auth';

const baseURL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const options = { baseURL, withCredentials: true, timeout: 15_000 };

// Cookie operations never use the response interceptor, preventing refresh loops.
export const authTransport = axios.create(options);
export const api = axios.create(options);
let refreshFlight: Promise<TokenData> | null = null;

export function refreshSession(): Promise<TokenData> {
  if (!refreshFlight) {
    const revision = useSession.getState().revision;
    refreshFlight = authTransport.post<ApiSuccess<TokenData>>('/auth/refresh')
      .then(({ data }) => {
        if (useSession.getState().revision !== revision) {
          throw new Error('Session changed during refresh');
        }
        useSession.getState().accept(data.data);
        return data.data;
      })
      .catch((error: unknown) => {
        if (useSession.getState().revision === revision) {
          const status = axios.isAxiosError(error) ? error.response?.status : undefined;
          if (status === 401) useSession.getState().clear();
          else useSession.getState().fail();
        }
        throw error;
      })
      .finally(() => { refreshFlight = null; });
  }
  return refreshFlight;
}

api.interceptors.request.use((config) => {
  const token = useSession.getState().accessToken;
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
  return config;
});

type RetryConfig = InternalAxiosRequestConfig & { sessionRetried?: boolean };
api.interceptors.response.use(undefined, async (error: unknown) => {
  if (!axios.isAxiosError(error)) throw error;
  const config = error.config as RetryConfig | undefined;
  if (error.response?.status !== 401 || !config) throw error;
  if (config.sessionRetried) {
    useSession.getState().clear();
    throw error;
  }
  config.sessionRetried = true;
  // A parallel request may already have renewed the token before this 401 arrives.
  const currentToken = useSession.getState().accessToken;
  if (!currentToken) throw error;
  if (config.headers.get('Authorization') === `Bearer ${currentToken}`) await refreshSession();
  const renewedToken = useSession.getState().accessToken;
  if (!renewedToken) throw error;
  config.headers = AxiosHeaders.from(config.headers);
  config.headers.set('Authorization', `Bearer ${renewedToken}`);
  return api.request(config);
});

export async function login(email: string, password: string) {
  const revision = useSession.getState().revision;
  const { data } = await authTransport.post<ApiSuccess<TokenData>>('/auth/login', { email, password });
  if (useSession.getState().revision === revision) useSession.getState().accept(data.data);
}

export async function logout() {
  await authTransport.post('/auth/logout');
  useSession.getState().clear();
}

export function loginError(error: unknown): string {
  if (axios.isAxiosError(error) && error.response?.status === 401) return 'Email hoặc mật khẩu không đúng.';
  if (axios.isAxiosError(error) && error.response?.status === 429) return 'Bạn đã thử quá nhiều lần. Vui lòng thử lại sau.';
  return 'Chưa thể kết nối để đăng nhập. Vui lòng thử lại.';
}
