import React from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box, 
  IconButton,
  Badge,
  Chip
} from '@mui/material';
import {
  Home,
  PlayArrow,
  Stop,
  Settings,
  Analytics,
  FiberManualRecord
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSession } from '../contexts/SessionContext';
import { useWebSocket } from '../contexts/WebSocketContext';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isTracking, selectedSport, startTracking, stopTracking } = useSession();
  const { isConnected } = useWebSocket();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <Home /> },
    { path: '/tracker', label: 'Live Tracker', icon: <PlayArrow /> },
    { path: '/analytics', label: 'Analytics', icon: <Analytics /> },
    { path: '/settings', label: 'Settings', icon: <Settings /> }
  ];

  const handleTrackingToggle = async () => {
    try {
      if (isTracking) {
        await stopTracking();
      } else {
        await startTracking();
      }
    } catch (error) {
      console.error('Error toggling tracking:', error);
    }
  };

  return (
    <AppBar position="sticky" elevation={2}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Multi-Sport Tracker
        </Typography>

        {/* Connection Status */}
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
          <Badge
            color={isConnected ? 'success' : 'error'}
            variant="dot"
            sx={{ mr: 1 }}
          >
            <FiberManualRecord fontSize="small" />
          </Badge>
          <Typography variant="body2" color="inherit">
            {isConnected ? 'Connected' : 'Disconnected'}
          </Typography>
        </Box>

        {/* Selected Sport */}
        <Chip
          label={selectedSport.toUpperCase()}
          variant="outlined"
          color="secondary"
          size="small"
          sx={{ mr: 2, color: 'white', borderColor: 'white' }}
        />

        {/* Navigation Items */}
        <Box sx={{ display: 'flex', mr: 2 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                mx: 0.5,
                backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.1)' : 'transparent'
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* Tracking Toggle */}
        <Button
          variant={isTracking ? 'contained' : 'outlined'}
          color={isTracking ? 'error' : 'success'}
          startIcon={isTracking ? <Stop /> : <PlayArrow />}
          onClick={handleTrackingToggle}
          disabled={!isConnected}
          sx={{
            color: isTracking ? 'white' : 'inherit',
            borderColor: isTracking ? 'error.main' : 'white'
          }}
        >
          {isTracking ? 'Stop' : 'Start'} Tracking
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
