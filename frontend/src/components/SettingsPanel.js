import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  Alert,
  TextField,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Paper
} from '@mui/material';
import {
  Save,
  Restore,
  VolumeUp,
  VolumeOff,
  Visibility,
  VisibilityOff,
  Vibration,
  Camera,
  Tune,
  Delete
} from '@mui/icons-material';
import { useSession } from '../contexts/SessionContext';

const SettingsPanel = () => {
  const { settings, selectedSport, updateSettings, setSelectedSport } = useSession();
  
  const [localSettings, setLocalSettings] = useState({
    // General Settings
    feedbackTypes: ['audio', 'visual'],
    sensitivity: 0.7,
    minConfidence: 0.8,
    
    // Camera Settings
    cameraSource: 0,
    resolution: '640x480',
    fps: 30,
    
    // Sport-specific Settings
    sportSettings: {
      basketball: {
        shotDetectionSensitivity: 0.8,
        minimumArcHeight: 0.3,
        basketPosition: 'auto'
      },
      tennis: {
        serveDetectionSensitivity: 0.7,
        minimumRacketSpeed: 15,
        courtPosition: 'baseline'
      },
      soccer: {
        kickDetectionSensitivity: 0.6,
        minimumBallSpeed: 10,
        goalPosition: 'auto'
      },
      golf: {
        swingDetectionSensitivity: 0.8,
        minimumClubSpeed: 20,
        ballPosition: 'tee'
      }
    },
    
    // Audio Settings
    audioVolume: 0.8,
    successSound: 'cheer',
    failureSound: 'buzzer',
    
    // Visual Settings
    showPoseOverlay: true,
    showConfidenceScore: true,
    overlayOpacity: 0.7,
    
    // Haptic Settings (future feature)
    hapticEnabled: false,
    hapticIntensity: 0.5,
    
    // Performance Settings
    processingQuality: 'medium',
    maxFPS: 30,
    
    // Data Settings
    saveRawData: false,
    autoExport: false,
    dataRetentionDays: 30
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const sports = ['basketball', 'tennis', 'soccer', 'golf'];
  const resolutions = ['320x240', '640x480', '1280x720', '1920x1080'];
  const soundOptions = ['cheer', 'bell', 'beep', 'buzzer', 'whistle'];
  const qualityOptions = ['low', 'medium', 'high'];

  useEffect(() => {
    // Load settings from session context
    if (settings) {
      setLocalSettings(prev => ({ ...prev, ...settings }));
    }
  }, [settings]);

  const handleSettingChange = (category, setting, value) => {
    setLocalSettings(prev => {
      const newSettings = { ...prev };
      if (category) {
        newSettings[category] = { ...newSettings[category], [setting]: value };
      } else {
        newSettings[setting] = value;
      }
      return newSettings;
    });
    setHasChanges(true);
  };

  const handleFeedbackTypeToggle = (type) => {
    const currentTypes = localSettings.feedbackTypes;
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    handleSettingChange(null, 'feedbackTypes', newTypes);
  };

  const handleSaveSettings = async () => {
    try {
      await updateSettings(localSettings);
      setHasChanges(false);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleResetSettings = () => {
    setLocalSettings({
      feedbackTypes: ['audio', 'visual'],
      sensitivity: 0.7,
      minConfidence: 0.8,
      cameraSource: 0,
      resolution: '640x480',
      fps: 30,
      sportSettings: {
        basketball: {
          shotDetectionSensitivity: 0.8,
          minimumArcHeight: 0.3,
          basketPosition: 'auto'
        },
        tennis: {
          serveDetectionSensitivity: 0.7,
          minimumRacketSpeed: 15,
          courtPosition: 'baseline'
        },
        soccer: {
          kickDetectionSensitivity: 0.6,
          minimumBallSpeed: 10,
          goalPosition: 'auto'
        },
        golf: {
          swingDetectionSensitivity: 0.8,
          minimumClubSpeed: 20,
          ballPosition: 'tee'
        }
      },
      audioVolume: 0.8,
      successSound: 'cheer',
      failureSound: 'buzzer',
      showPoseOverlay: true,
      showConfidenceScore: true,
      overlayOpacity: 0.7,
      hapticEnabled: false,
      hapticIntensity: 0.5,
      processingQuality: 'medium',
      maxFPS: 30,
      saveRawData: false,
      autoExport: false,
      dataRetentionDays: 30
    });
    setHasChanges(true);
  };

  const SettingCard = ({ title, children }) => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {children}
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Settings
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Restore />}
            onClick={handleResetSettings}
          >
            Reset to Defaults
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSaveSettings}
            disabled={!hasChanges}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      {/* Save Status */}
      {saveStatus && (
        <Alert 
          severity={saveStatus === 'success' ? 'success' : 'error'} 
          sx={{ mb: 3 }}
        >
          {saveStatus === 'success' ? 'Settings saved successfully!' : 'Failed to save settings.'}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <SettingCard title="General Settings">
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Selected Sport
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {sports.map((sport) => (
                  <Chip
                    key={sport}
                    label={sport.charAt(0).toUpperCase() + sport.slice(1)}
                    clickable
                    color={selectedSport === sport ? 'primary' : 'default'}
                    variant={selectedSport === sport ? 'filled' : 'outlined'}
                    onClick={() => setSelectedSport(sport)}
                  />
                ))}
              </Box>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Feedback Types
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localSettings.feedbackTypes.includes('audio')}
                      onChange={() => handleFeedbackTypeToggle('audio')}
                      icon={<VolumeOff />}
                      checkedIcon={<VolumeUp />}
                    />
                  }
                  label="Audio Feedback"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={localSettings.feedbackTypes.includes('visual')}
                      onChange={() => handleFeedbackTypeToggle('visual')}
                      icon={<VisibilityOff />}
                      checkedIcon={<Visibility />}
                    />
                  }
                  label="Visual Feedback"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={localSettings.feedbackTypes.includes('haptic')}
                      onChange={() => handleFeedbackTypeToggle('haptic')}
                      icon={<Vibration />}
                      checkedIcon={<Vibration />}
                    />
                  }
                  label="Haptic Feedback (Coming Soon)"
                  disabled
                />
              </Box>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Detection Sensitivity: {(localSettings.sensitivity * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={localSettings.sensitivity}
                onChange={(_, value) => handleSettingChange(null, 'sensitivity', value)}
                min={0.1}
                max={1.0}
                step={0.1}
                marks
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Minimum Confidence: {(localSettings.minConfidence * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={localSettings.minConfidence}
                onChange={(_, value) => handleSettingChange(null, 'minConfidence', value)}
                min={0.5}
                max={1.0}
                step={0.05}
                marks
              />
            </Box>
          </SettingCard>

          {/* Audio Settings */}
          <SettingCard title="Audio Settings">
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Volume: {(localSettings.audioVolume * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={localSettings.audioVolume}
                onChange={(_, value) => handleSettingChange(null, 'audioVolume', value)}
                min={0}
                max={1}
                step={0.1}
                disabled={!localSettings.feedbackTypes.includes('audio')}
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Success Sound</InputLabel>
                  <Select
                    value={localSettings.successSound}
                    label="Success Sound"
                    onChange={(e) => handleSettingChange(null, 'successSound', e.target.value)}
                    disabled={!localSettings.feedbackTypes.includes('audio')}
                  >
                    {soundOptions.map((sound) => (
                      <MenuItem key={sound} value={sound}>
                        {sound.charAt(0).toUpperCase() + sound.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Failure Sound</InputLabel>
                  <Select
                    value={localSettings.failureSound}
                    label="Failure Sound"
                    onChange={(e) => handleSettingChange(null, 'failureSound', e.target.value)}
                    disabled={!localSettings.feedbackTypes.includes('audio')}
                  >
                    {soundOptions.map((sound) => (
                      <MenuItem key={sound} value={sound}>
                        {sound.charAt(0).toUpperCase() + sound.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </SettingCard>
        </Grid>

        {/* Camera and Performance Settings */}
        <Grid item xs={12} md={6}>
          <SettingCard title="Camera Settings">
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6}>
                <TextField
                  label="Camera Source"
                  type="number"
                  size="small"
                  fullWidth
                  value={localSettings.cameraSource}
                  onChange={(e) => handleSettingChange(null, 'cameraSource', parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0, max: 10 }}
                />
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Resolution</InputLabel>
                  <Select
                    value={localSettings.resolution}
                    label="Resolution"
                    onChange={(e) => handleSettingChange(null, 'resolution', e.target.value)}
                  >
                    {resolutions.map((res) => (
                      <MenuItem key={res} value={res}>
                        {res}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Frame Rate: {localSettings.fps} FPS
              </Typography>
              <Slider
                value={localSettings.fps}
                onChange={(_, value) => handleSettingChange(null, 'fps', value)}
                min={15}
                max={60}
                step={5}
                marks
              />
            </Box>
          </SettingCard>

          {/* Visual Settings */}
          <SettingCard title="Visual Settings">
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={localSettings.showPoseOverlay}
                    onChange={(e) => handleSettingChange(null, 'showPoseOverlay', e.target.checked)}
                    disabled={!localSettings.feedbackTypes.includes('visual')}
                  />
                }
                label="Show Pose Overlay"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={localSettings.showConfidenceScore}
                    onChange={(e) => handleSettingChange(null, 'showConfidenceScore', e.target.checked)}
                    disabled={!localSettings.feedbackTypes.includes('visual')}
                  />
                }
                label="Show Confidence Score"
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Overlay Opacity: {(localSettings.overlayOpacity * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={localSettings.overlayOpacity}
                onChange={(_, value) => handleSettingChange(null, 'overlayOpacity', value)}
                min={0.1}
                max={1.0}
                step={0.1}
                disabled={!localSettings.feedbackTypes.includes('visual')}
              />
            </Box>
          </SettingCard>

          {/* Performance Settings */}
          <SettingCard title="Performance Settings">
            <FormControl fullWidth size="small" sx={{ mb: 3 }}>
              <InputLabel>Processing Quality</InputLabel>
              <Select
                value={localSettings.processingQuality}
                label="Processing Quality"
                onChange={(e) => handleSettingChange(null, 'processingQuality', e.target.value)}
              >
                {qualityOptions.map((quality) => (
                  <MenuItem key={quality} value={quality}>
                    {quality.charAt(0).toUpperCase() + quality.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Max Processing FPS: {localSettings.maxFPS}
              </Typography>
              <Slider
                value={localSettings.maxFPS}
                onChange={(_, value) => handleSettingChange(null, 'maxFPS', value)}
                min={10}
                max={60}
                step={5}
                marks
              />
            </Box>
          </SettingCard>
        </Grid>

        {/* Sport-Specific Settings */}
        <Grid item xs={12}>
          <SettingCard title={`${selectedSport.charAt(0).toUpperCase() + selectedSport.slice(1)} Specific Settings`}>
            {selectedSport && localSettings.sportSettings[selectedSport] && (
              <Grid container spacing={3}>
                {Object.entries(localSettings.sportSettings[selectedSport]).map(([key, value]) => (
                  <Grid item xs={12} md={4} key={key}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                      </Typography>
                      {typeof value === 'number' ? (
                        <Slider
                          value={value}
                          onChange={(_, newValue) => 
                            handleSettingChange('sportSettings', selectedSport, {
                              ...localSettings.sportSettings[selectedSport],
                              [key]: newValue
                            })
                          }
                          min={0}
                          max={key.includes('Speed') ? 50 : 1}
                          step={key.includes('Speed') ? 1 : 0.1}
                        />
                      ) : (
                        <TextField
                          value={value}
                          onChange={(e) =>
                            handleSettingChange('sportSettings', selectedSport, {
                              ...localSettings.sportSettings[selectedSport],
                              [key]: e.target.value
                            })
                          }
                          size="small"
                          fullWidth
                        />
                      )}
                    </Box>
                  </Grid>
                ))}
              </Grid>
            )}
          </SettingCard>
        </Grid>

        {/* Data Settings */}
        <Grid item xs={12}>
          <SettingCard title="Data & Privacy Settings">
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localSettings.saveRawData}
                      onChange={(e) => handleSettingChange(null, 'saveRawData', e.target.checked)}
                    />
                  }
                  label="Save Raw Video Data"
                />
                <Typography variant="body2" color="text.secondary">
                  Store original camera frames for analysis
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localSettings.autoExport}
                      onChange={(e) => handleSettingChange(null, 'autoExport', e.target.checked)}
                    />
                  }
                  label="Auto Export Sessions"
                />
                <Typography variant="body2" color="text.secondary">
                  Automatically export session data
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  label="Data Retention (Days)"
                  type="number"
                  size="small"
                  value={localSettings.dataRetentionDays}
                  onChange={(e) => handleSettingChange(null, 'dataRetentionDays', parseInt(e.target.value) || 30)}
                  inputProps={{ min: 1, max: 365 }}
                />
                <Typography variant="body2" color="text.secondary">
                  How long to keep session data
                </Typography>
              </Grid>
            </Grid>
          </SettingCard>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SettingsPanel;
