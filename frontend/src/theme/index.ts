import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: { main: '#0d9488', dark: '#065f53', contrastText: '#fff' },
    secondary: { main: '#2563eb' },
    warning: { main: '#ea580c' },
    background: { default: '#fafaf8', paper: '#ffffff' },
    text: { primary: '#1a1a1a', secondary: '#6b6966' },
    divider: '#e8e6e1',
  },
  typography: {
    fontFamily: 'Outfit, "Segoe UI", system-ui, sans-serif',
    h1: { fontSize: '2rem', fontWeight: 700, lineHeight: 1.2 },
    h2: { fontSize: '1.5rem', fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { minWidth: 320 },
        ':focus-visible': { outline: '2px solid #065f53', outlineOffset: 3 },
        '@media (prefers-reduced-motion: reduce)': {
          '*, *::before, *::after': {
            animation: 'none !important', transition: 'none !important', scrollBehavior: 'auto !important',
          },
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { minHeight: 44 },
        containedPrimary: { backgroundColor: '#087f73', '&:hover': { backgroundColor: '#065f53' } },
        outlinedPrimary: { color: '#065f53' },
        textPrimary: { color: '#065f53' },
      },
    },
    MuiInputLabel: { styleOverrides: { root: { '&.Mui-focused': { color: '#065f53' } } } },
    MuiPaper: { defaultProps: { elevation: 0 } },
    MuiTextField: { defaultProps: { fullWidth: true } },
  },
});
