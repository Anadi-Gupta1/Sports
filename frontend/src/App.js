import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Button, Container } from '@mui/material';
import Dashboard from './components/Dashboard';
import SessionManager from './components/SessionManager';
import RealTimeTracker from './components/RealTimeTracker';
import SettingsPanel from './components/SettingsPanel';
import Analytics from './components/Analytics';
import Navigation from './components/Navigation';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { SessionProvider } from './contexts/SessionContext';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  const [currentRoute, setCurrentRoute] = useState('/dashboard');

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider>
        <SessionProvider>
          <Router>
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <AppBar position="static" elevation={1}>
                <Toolbar>
                  <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    Multi-Sport Action Tracker
                  </Typography>
                  <Navigation currentRoute={currentRoute} setCurrentRoute={setCurrentRoute} />
                </Toolbar>
              </AppBar>
              
              <Container maxWidth="xl" sx={{ flex: 1, py: 3 }}>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/session" element={<SessionManager />} />
                  <Route path="/tracker" element={<RealTimeTracker />} />
                  <Route path="/settings" element={<SettingsPanel />} />
                  <Route path="/analytics" element={<Analytics />} />
                </Routes>
              </Container>
            </Box>
          </Router>
        </SessionProvider>
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;
