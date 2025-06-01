import React, { useEffect, useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  IconButton,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Paper,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  PlayArrow,
  Sports,
  Timer,
  EmojiEvents,
  Refresh
} from '@mui/icons-material';
import { useSession } from '../contexts/SessionContext';
import { useWebSocket } from '../contexts/WebSocketContext';

const Dashboard = () => {
  const { 
    sessions, 
    currentSession, 
    stats, 
    selectedSport, 
    isTracking,
    loading,
    getSessions 
  } = useSession();
  const { lastMessage, isConnected } = useWebSocket();
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    // Process real-time messages for recent activity
    if (lastMessage && lastMessage.type === 'action_detected') {
      const newActivity = {
        id: Date.now(),
        type: lastMessage.data.action,
        success: lastMessage.data.successful,
        score: lastMessage.data.confidence,
        timestamp: new Date().toLocaleTimeString(),
        sport: selectedSport
      };
      
      setRecentActivity(prev => [newActivity, ...prev.slice(0, 9)]); // Keep last 10
    }
  }, [lastMessage, selectedSport]);

  const StatCard = ({ title, value, subtitle, icon, trend, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: `${color}.main`, mr: 2 }}>
            {icon}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="div" color={`${color}.main`}>
              {value}
            </Typography>
            <Typography variant="h6" color="text.primary">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {trend && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {trend > 0 ? (
                <TrendingUp color="success" />
              ) : (
                <TrendingDown color="error" />
              )}
              <Typography
                variant="body2"
                color={trend > 0 ? 'success.main' : 'error.main'}
                sx={{ ml: 0.5 }}
              >
                {Math.abs(trend)}%
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  const ActivityItem = ({ activity }) => (
    <ListItem>
      <ListItemAvatar>
        <Avatar
          sx={{
            bgcolor: activity.success ? 'success.main' : 'error.main',
            width: 32,
            height: 32
          }}
        >
          <Sports fontSize="small" />
        </Avatar>
      </ListItemAvatar>
      <ListItemText
        primary={`${activity.type} - ${activity.sport}`}
        secondary={`${activity.timestamp} • Score: ${(activity.score * 100).toFixed(1)}%`}
      />
      <ListItemSecondaryAction>
        <Chip
          label={activity.success ? 'Success' : 'Miss'}
          color={activity.success ? 'success' : 'error'}
          size="small"
        />
      </ListItemSecondaryAction>
    </ListItem>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            label={`Sport: ${selectedSport.toUpperCase()}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={isTracking ? 'Tracking Active' : 'Tracking Stopped'}
            color={isTracking ? 'success' : 'default'}
            icon={isTracking ? <PlayArrow /> : <Timer />}
          />
          <IconButton onClick={() => getSessions()} disabled={loading}>
            {loading ? <CircularProgress size={24} /> : <Refresh />}
          </IconButton>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Actions"
            value={stats.totalActions}
            subtitle="All time"
            icon={<Sports />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Success Rate"
            value={`${stats.successRate.toFixed(1)}%`}
            subtitle={`${stats.successfulActions} successful`}
            icon={<EmojiEvents />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Average Score"
            value={`${(stats.averageScore * 100).toFixed(1)}%`}
            subtitle="Confidence level"
            icon={<TrendingUp />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Sessions"
            value={sessions.length}
            subtitle={currentSession ? 'Session active' : 'No active session'}
            icon={<Timer />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Content Grid */}
      <Grid container spacing={3}>
        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <PlayArrow sx={{ mr: 1 }} />
                Recent Activity
                {!isConnected && (
                  <Chip
                    label="Offline"
                    color="error"
                    size="small"
                    sx={{ ml: 2 }}
                  />
                )}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {recentActivity.length > 0 ? (
                <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {recentActivity.map((activity, index) => (
                    <React.Fragment key={activity.id}>
                      <ActivityItem activity={activity} />
                      {index < recentActivity.length - 1 && <Divider variant="inset" component="li" />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {isTracking ? 'Waiting for activity...' : 'Start tracking to see activity'}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Sessions */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Timer sx={{ mr: 1 }} />
                Recent Sessions
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {sessions.length > 0 ? (
                <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {sessions.slice(0, 5).map((session, index) => (
                    <React.Fragment key={session.id}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'primary.main' }}>
                            <Sports />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={`${session.sport} Session`}
                          secondary={`${new Date(session.created_at).toLocaleDateString()} • ${session.total_actions || 0} actions`}
                        />
                        <ListItemSecondaryAction>
                          <Chip
                            label={session.is_active ? 'Active' : 'Completed'}
                            color={session.is_active ? 'success' : 'default'}
                            size="small"
                          />
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < Math.min(sessions.length, 5) - 1 && <Divider variant="inset" component="li" />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    No sessions yet. Create your first session to get started!
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Overview */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Performance Overview
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Success Rate Progress
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={stats.successRate}
                      color="success"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {stats.successRate.toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Average Confidence
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={stats.averageScore * 100}
                      color="info"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {(stats.averageScore * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Actions Completed
                </Typography>
                <Typography variant="h4" color="primary.main">
                  {stats.totalActions}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
