import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { makeRouter } from './router';
import { theme } from './theme';
import { queryClient } from './services/queryClient';
import { useSession } from './stores/session';

// Drop cached seller data as soon as the session identity changes or is lost.
useSession.subscribe((state, previous) => {
  if (state.user?.id !== previous.user?.id || state.status !== 'authenticated') queryClient.clear();
});

const router = makeRouter();
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
