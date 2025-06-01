import React, { useEffect, useState, useRef } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Chip,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress,
  IconButton,
  CircularProgress,
  Avatar,
  Badge
} from '@mui/material';
import {
  Videocam,
  VideocamOff,
  FiberManualRecord,
  CheckCircle,
  Cancel,
  TrendingUp,
  Refresh,
  Fullscreen,
  FullscreenExit
} from '@mui/icons-material';
import { useSession } from '../contexts/SessionContext';
import { useWebSocket } from '../contexts/WebSocketContext';

const RealTimeTracker = () => {
  const {
    currentSession,
    isTracking,
    selectedSport,
    stats,
    startTracking,
    stopTracking,
    updateStats
  } = useSession();
  
  const { lastMessage, isConnected, sendMessage } = useWebSocket();
  
  const [cameraActive, setCameraActive] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [recentActions, setRecentActions] = useState([]);
  const [currentFeedback, setCurrentFeedback] = useState(null);
  const [performanceData, setPerformanceData] = useState({
    streak: 0,
    lastAction: null,
    sessionActions: 0,
    sessionSuccesses: 0
  });

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Process real-time WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'action_detected':
          handleActionDetected(lastMessage.data);
          break;
        case 'feedback':
          setCurrentFeedback(lastMessage.data);
          setTimeout(() => setCurrentFeedback(null), 3000);
          break;
        case 'camera_status':
          setCameraActive(lastMessage.data.active);
          break;
        case 'tracking_status':
          // Handle tracking status updates
          break;
        default:
          break;
      }
    }
  }, [lastMessage]);

  const handleActionDetected = (actionData) => {
    const newAction = {
      id: Date.now(),
      type: actionData.action,
      successful: actionData.successful,
      confidence: actionData.confidence,
      timestamp: new Date(),
      details: actionData.details || {}
    };

    setRecentActions(prev => [newAction, ...prev.slice(0, 9)]);
    
    // Update performance data
    setPerformanceData(prev => ({
      ...prev,
      lastAction: newAction,
      sessionActions: prev.sessionActions + 1,
      sessionSuccesses: prev.sessionSuccesses + (newAction.successful ? 1 : 0),
      streak: newAction.successful ? prev.streak + 1 : 0
    }));

    // Update global stats
    updateStats({
      totalActions: stats.totalActions + 1,
      successfulActions: stats.successfulActions + (newAction.successful ? 1 : 0),
      successRate: ((stats.successfulActions + (newAction.successful ? 1 : 0)) / (stats.totalActions + 1)) * 100,
      averageScore: ((stats.averageScore * stats.totalActions) + newAction.confidence) / (stats.totalActions + 1)
    });
  };

  const handleStartTracking = async () => {
    try {
      await startTracking();
      // Request camera activation
      sendMessage({
        type: 'camera_control',
        action: 'start'
      });
    } catch (error) {
      console.error('Failed to start tracking:', error);
    }
  };

  const handleStopTracking = async () => {
    try {
      await stopTracking();
      sendMessage({
        type: 'camera_control',
        action: 'stop'
      });
      setCameraActive(false);
    } catch (error) {
      console.error('Failed to stop tracking:', error);
    }
  };

  const toggleFullscreen = () => {
    if (!fullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setFullscreen(!fullscreen);
  };

  const ActionItem = ({ action }) => (
    <ListItem>
      <ListItemIcon>
        <Avatar
          sx={{
            bgcolor: action.successful ? 'success.main' : 'error.main',
            width: 32,
            height: 32
          }}
        >
          {action.successful ? <CheckCircle fontSize="small" /> : <Cancel fontSize="small" />}
        </Avatar>
      </ListItemIcon>
      <ListItemText
        primary={`${action.type} - ${(action.confidence * 100).toFixed(1)}%`}
        secondary={action.timestamp.toLocaleTimeString()}
      />
    </ListItem>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 3 }} ref={containerRef}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Real-Time Tracker
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={selectedSport.toUpperCase()}
            color="primary"
            variant="outlined"
          />
          <Badge
            color={isConnected ? 'success' : 'error'}
            variant="dot"
          >
            <Chip
              label={isConnected ? 'Connected' : 'Disconnected'}
              color={isConnected ? 'success' : 'error'}
              size="small"
            />
          </Badge>
          <IconButton onClick={toggleFullscreen}>
            {fullscreen ? <FullscreenExit /> : <Fullscreen />}
          </IconButton>
        </Box>
      </Box>

      {/* Session Status */}
      {!currentSession && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          No active session. Please create or select a session from the Session Manager to start tracking.
        </Alert>
      )}

      {/* Feedback Display */}
      {currentFeedback && (
        <Alert 
          severity={currentFeedback.type === 'success' ? 'success' : 'info'} 
          sx={{ mb: 3 }}
        >
          {currentFeedback.message}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Video Feed */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: fullscreen ? '80vh' : 500 }}>
            <CardContent sx={{ height: '100%', p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Camera Feed
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Chip
                    icon={cameraActive ? <Videocam /> : <VideocamOff />}
                    label={cameraActive ? 'Camera Active' : 'Camera Inactive'}
                    color={cameraActive ? 'success' : 'default'}
                    size="small"
                  />
                  <Chip
                    icon={<FiberManualRecord />}
                    label={isTracking ? 'Tracking' : 'Stopped'}
                    color={isTracking ? 'error' : 'default'}
                    size="small"
                  />
                </Box>
              </Box>

              {/* Video Container */}
              <Box 
                sx={{ 
                  position: 'relative',
                  height: 'calc(100% - 60px)',
                  bgcolor: 'black',
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {cameraActive ? (
                  <>
                    <video
                      ref={videoRef}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain'
                      }}
                      autoPlay
                      muted
                    />
                    <canvas
                      ref={canvasRef}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        pointerEvents: 'none'
                      }}
                    />
                  </>
                ) : (
                  <Box sx={{ textAlign: 'center', color: 'white' }}>
                    <VideocamOff sx={{ fontSize: 64, mb: 2 }} />
                    <Typography variant="h6">
                      Camera not active
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {isTracking ? 'Starting camera...' : 'Start tracking to activate camera'}
                    </Typography>
                  </Box>
                )}
              </Box>

              {/* Control Buttons */}
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                {isTracking ? (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<VideocamOff />}
                    onClick={handleStopTracking}
                    size="large"
                  >
                    Stop Tracking
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<Videocam />}
                    onClick={handleStartTracking}
                    disabled={!isConnected || !currentSession}
                    size="large"
                  >
                    Start Tracking
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Performance Stats */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Performance
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="h4" color="primary.main">
                    {performanceData.sessionActions}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Actions
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="h4" color="success.main">
                    {performanceData.sessionSuccesses}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Successful
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="h4" color="warning.main">
                    {performanceData.streak}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Current Streak
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="h4" color="info.main">
                    {performanceData.sessionActions > 0 
                      ? ((performanceData.sessionSuccesses / performanceData.sessionActions) * 100).toFixed(1)
                      : 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Success Rate
                  </Typography>
                </Grid>
              </Grid>
              
              {currentSession && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Progress to Target ({currentSession.target_actions} actions)
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(performanceData.sessionActions / currentSession.target_actions) * 100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Recent Actions */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Actions
              </Typography>
              {recentActions.length > 0 ? (
                <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {recentActions.map((action) => (
                    <ActionItem key={action.id} action={action} />
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    {isTracking ? 'Waiting for actions...' : 'Start tracking to see actions'}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default RealTimeTracker;
