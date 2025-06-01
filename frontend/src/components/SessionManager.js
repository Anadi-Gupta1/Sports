import React, { useState, useEffect } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  PlayArrow,
  Stop,
  Refresh
} from '@mui/icons-material';
import { useSession } from '../contexts/SessionContext';

const SessionManager = () => {
  const {
    sessions,
    currentSession,
    selectedSport,
    isTracking,
    loading,
    error,
    createSession,
    getSessions,
    getSession,
    startTracking,
    stopTracking,
    setSelectedSport,
    clearError
  } = useSession();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [newSessionData, setNewSessionData] = useState({
    name: '',
    sport: 'basketball',
    description: '',
    target_actions: 50,
    settings: {
      feedbackTypes: ['audio', 'visual'],
      sensitivity: 0.7,
      minConfidence: 0.8
    }
  });

  const sports = ['basketball', 'tennis', 'soccer', 'golf'];

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleCreateSession = async () => {
    try {
      const sessionData = {
        ...newSessionData,
        name: newSessionData.name || `${newSessionData.sport} Session ${new Date().toLocaleDateString()}`
      };
      
      await createSession(sessionData);
      setDialogOpen(false);
      setNewSessionData({
        name: '',
        sport: 'basketball',
        description: '',
        target_actions: 50,
        settings: {
          feedbackTypes: ['audio', 'visual'],
          sensitivity: 0.7,
          minConfidence: 0.8
        }
      });
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleStartTracking = async (sessionId) => {
    try {
      if (sessionId && sessionId !== currentSession?.id) {
        await getSession(sessionId);
      }
      await startTracking();
    } catch (error) {
      console.error('Failed to start tracking:', error);
    }
  };

  const handleStopTracking = async () => {
    try {
      await stopTracking();
    } catch (error) {
      console.error('Failed to stop tracking:', error);
    }
  };

  const handleSportChange = (sport) => {
    setSelectedSport(sport);
    setNewSessionData(prev => ({ ...prev, sport }));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Session Manager
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => getSessions()}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setDialogOpen(true)}
          >
            New Session
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={clearError}>
          {error}
        </Alert>
      )}

      {/* Sport Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Sport Selection
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {sports.map((sport) => (
              <Chip
                key={sport}
                label={sport.charAt(0).toUpperCase() + sport.slice(1)}
                clickable
                color={selectedSport === sport ? 'primary' : 'default'}
                variant={selectedSport === sport ? 'filled' : 'outlined'}
                onClick={() => handleSportChange(sport)}
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Current Session Status */}
      {currentSession && (
        <Card sx={{ mb: 3, bgcolor: isTracking ? 'success.light' : 'grey.100' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h6">
                  Current Session: {currentSession.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sport: {currentSession.sport} • Created: {new Date(currentSession.created_at).toLocaleString()}
                </Typography>
                {currentSession.description && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {currentSession.description}
                  </Typography>
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {isTracking ? (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<Stop />}
                    onClick={handleStopTracking}
                  >
                    Stop Tracking
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<PlayArrow />}
                    onClick={() => handleStartTracking(currentSession.id)}
                  >
                    Start Tracking
                  </Button>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Sessions List */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            All Sessions
          </Typography>
          {sessions.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary">
                No sessions found. Create your first session to get started!
              </Typography>
            </Box>
          ) : (
            <List>
              {sessions.map((session, index) => (
                <React.Fragment key={session.id}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {session.name}
                          </Typography>
                          <Chip
                            label={session.sport}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                          {session.is_active && (
                            <Chip
                              label="Active"
                              size="small"
                              color="success"
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Created: {new Date(session.created_at).toLocaleString()}
                          </Typography>
                          {session.description && (
                            <Typography variant="body2" color="text.secondary">
                              {session.description}
                            </Typography>
                          )}
                          <Typography variant="body2" color="text.secondary">
                            Target: {session.target_actions} actions • 
                            Completed: {session.total_actions || 0} actions
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton
                          edge="end"
                          onClick={() => handleStartTracking(session.id)}
                          disabled={isTracking && currentSession?.id === session.id}
                          color="primary"
                        >
                          <PlayArrow />
                        </IconButton>
                        <IconButton edge="end" color="default">
                          <Edit />
                        </IconButton>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < sessions.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Create Session Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Session</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Session Name"
              fullWidth
              value={newSessionData.name}
              onChange={(e) => setNewSessionData(prev => ({ ...prev, name: e.target.value }))}
              placeholder={`${newSessionData.sport} Session ${new Date().toLocaleDateString()}`}
            />
            
            <FormControl fullWidth>
              <InputLabel>Sport</InputLabel>
              <Select
                value={newSessionData.sport}
                label="Sport"
                onChange={(e) => setNewSessionData(prev => ({ ...prev, sport: e.target.value }))}
              >
                {sports.map((sport) => (
                  <MenuItem key={sport} value={sport}>
                    {sport.charAt(0).toUpperCase() + sport.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Description (Optional)"
              fullWidth
              multiline
              rows={2}
              value={newSessionData.description}
              onChange={(e) => setNewSessionData(prev => ({ ...prev, description: e.target.value }))}
            />

            <TextField
              label="Target Actions"
              type="number"
              fullWidth
              value={newSessionData.target_actions}
              onChange={(e) => setNewSessionData(prev => ({ ...prev, target_actions: parseInt(e.target.value) || 50 }))}
              inputProps={{ min: 1, max: 1000 }}
            />

            <Typography variant="subtitle2" sx={{ mt: 1 }}>
              Feedback Settings
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newSessionData.settings.feedbackTypes.includes('audio')}
                    onChange={(e) => {
                      const feedbackTypes = e.target.checked
                        ? [...newSessionData.settings.feedbackTypes, 'audio']
                        : newSessionData.settings.feedbackTypes.filter(type => type !== 'audio');
                      setNewSessionData(prev => ({
                        ...prev,
                        settings: { ...prev.settings, feedbackTypes }
                      }));
                    }}
                  />
                }
                label="Audio Feedback"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={newSessionData.settings.feedbackTypes.includes('visual')}
                    onChange={(e) => {
                      const feedbackTypes = e.target.checked
                        ? [...newSessionData.settings.feedbackTypes, 'visual']
                        : newSessionData.settings.feedbackTypes.filter(type => type !== 'visual');
                      setNewSessionData(prev => ({
                        ...prev,
                        settings: { ...prev.settings, feedbackTypes }
                      }));
                    }}
                  />
                }
                label="Visual Feedback"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateSession} variant="contained">
            Create Session
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SessionManager;
