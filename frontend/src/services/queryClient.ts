import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, error) => {
        if (axios.isAxiosError(error) && error.response && error.response.status < 500) return false;
        return count < 1;
      },
      refetchOnReconnect: true,
    },
    mutations: { retry: false },
  },
});
