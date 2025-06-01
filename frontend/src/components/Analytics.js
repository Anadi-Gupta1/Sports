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
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Visibility,
  Download,
  Refresh,
  DateRange,
  Sports,
  EmojiEvents,
  Timer,
  Assessment
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useSession } from '../contexts/SessionContext';

const Analytics = () => {
  const {
    sessions,
    getAnalytics,
    selectedSport,
    setSelectedSport,
    loading,
    error
  } = useSession();

  const [analyticsData, setAnalyticsData] = useState(null);
  const [selectedSession, setSelectedSession] = useState('all');
  const [timeRange, setTimeRange] = useState('7days');
  const [chartType, setChartType] = useState('line');
  const [detailsDialog, setDetailsDialog] = useState({ open: false, session: null });

  const timeRanges = [
    { value: '1day', label: 'Last 24 Hours' },
    { value: '7days', label: 'Last 7 Days' },
    { value: '30days', label: 'Last 30 Days' },
    { value: '90days', label: 'Last 3 Months' },
    { value: 'all', label: 'All Time' }
  ];

  const sports = ['all', 'basketball', 'tennis', 'soccer', 'golf'];

  useEffect(() => {
    loadAnalytics();
  }, [selectedSession, timeRange, selectedSport]);

  const loadAnalytics = async () => {
    try {
      let data;
      if (selectedSession === 'all') {
        // Aggregate data from all sessions
        data = await aggregateSessionData();
      } else {
        data = await getAnalytics(selectedSession);
      }
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const aggregateSessionData = async () => {
    const filteredSessions = sessions.filter(session => {
      const sessionDate = new Date(session.created_at);
      const now = new Date();
      const timeDiff = now - sessionDate;
      
      switch (timeRange) {
        case '1day':
          return timeDiff <= 24 * 60 * 60 * 1000;
        case '7days':
          return timeDiff <= 7 * 24 * 60 * 60 * 1000;
        case '30days':
          return timeDiff <= 30 * 24 * 60 * 60 * 1000;
        case '90days':
          return timeDiff <= 90 * 24 * 60 * 60 * 1000;
        default:
          return true;
      }
    }).filter(session => 
      selectedSport === 'all' || session.sport === selectedSport
    );

    // Aggregate performance data
    const totalActions = filteredSessions.reduce((sum, session) => sum + (session.total_actions || 0), 0);
    const totalSuccesses = filteredSessions.reduce((sum, session) => sum + (session.successful_actions || 0), 0);
    const averageConfidence = filteredSessions.reduce((sum, session) => sum + (session.average_confidence || 0), 0) / filteredSessions.length || 0;

    // Generate timeline data
    const timelineData = filteredSessions.map(session => ({
      date: new Date(session.created_at).toLocaleDateString(),
      actions: session.total_actions || 0,
      successRate: session.total_actions ? ((session.successful_actions || 0) / session.total_actions * 100) : 0,
      confidence: (session.average_confidence || 0) * 100
    }));

    // Sport distribution
    const sportDistribution = sessions.reduce((acc, session) => {
      acc[session.sport] = (acc[session.sport] || 0) + 1;
      return acc;
    }, {});

    return {
      summary: {
        totalSessions: filteredSessions.length,
        totalActions,
        totalSuccesses,
        successRate: totalActions ? (totalSuccesses / totalActions * 100) : 0,
        averageConfidence: averageConfidence * 100,
        improvementTrend: calculateTrend(timelineData)
      },
      timeline: timelineData,
      sportDistribution: Object.entries(sportDistribution).map(([sport, count]) => ({
        sport,
        count,
        percentage: (count / sessions.length * 100)
      })),
      sessions: filteredSessions
    };
  };

  const calculateTrend = (data) => {
    if (data.length < 2) return 0;
    const recent = data.slice(-3).reduce((sum, item) => sum + item.successRate, 0) / 3;
    const earlier = data.slice(0, Math.max(1, data.length - 3)).reduce((sum, item) => sum + item.successRate, 0) / Math.max(1, data.length - 3);
    return recent - earlier;
  };

  const formatNumber = (num) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const StatCard = ({ title, value, subtitle, icon, trend, color = 'primary' }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" color={`${color}.main`}>
              {value}
            </Typography>
            <Typography variant="h6">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {icon}
            {trend !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {trend > 0 ? (
                  <TrendingUp color="success" fontSize="small" />
                ) : trend < 0 ? (
                  <TrendingDown color="error" fontSize="small" />
                ) : null}
                <Typography
                  variant="caption"
                  color={trend > 0 ? 'success.main' : trend < 0 ? 'error.main' : 'text.secondary'}
                >
                  {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading && !analyticsData) {
    return (
      <Container maxWidth="xl" sx={{ py: 3, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading analytics...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Analytics Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sport</InputLabel>
            <Select
              value={selectedSport === 'all' ? 'all' : selectedSport}
              label="Sport"
              onChange={(e) => setSelectedSport(e.target.value)}
            >
              {sports.map((sport) => (
                <MenuItem key={sport} value={sport}>
                  {sport === 'all' ? 'All Sports' : sport.charAt(0).toUpperCase() + sport.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              {timeRanges.map((range) => (
                <MenuItem key={range.value} value={range.value}>
                  {range.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadAnalytics}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {analyticsData ? (
        <>
          {/* Summary Stats */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Sessions"
                value={analyticsData.summary.totalSessions}
                icon={<Timer />}
                color="primary"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Actions"
                value={formatNumber(analyticsData.summary.totalActions)}
                icon={<Sports />}
                color="info"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Success Rate"
                value={`${analyticsData.summary.successRate.toFixed(1)}%`}
                subtitle={`${analyticsData.summary.totalSuccesses} successful`}
                icon={<EmojiEvents />}
                trend={analyticsData.summary.improvementTrend}
                color="success"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Avg Confidence"
                value={`${analyticsData.summary.averageConfidence.toFixed(1)}%`}
                icon={<Assessment />}
                color="warning"
              />
            </Grid>
          </Grid>

          {/* Charts */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {/* Performance Timeline */}
            <Grid item xs={12} lg={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Over Time
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analyticsData.timeline}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="successRate"
                          stroke="#8884d8"
                          strokeWidth={2}
                          name="Success Rate (%)"
                        />
                        <Line
                          type="monotone"
                          dataKey="confidence"
                          stroke="#82ca9d"
                          strokeWidth={2}
                          name="Confidence (%)"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Sport Distribution */}
            <Grid item xs={12} lg={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Sport Distribution
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={analyticsData.sportDistribution}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ sport, percentage }) => `${sport} (${percentage.toFixed(1)}%)`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="count"
                        >
                          {analyticsData.sportDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Actions by Day */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Daily Activity
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analyticsData.timeline}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="actions" fill="#8884d8" name="Actions" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Sessions Table */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Details
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Sport</TableCell>
                      <TableCell>Duration</TableCell>
                      <TableCell>Actions</TableCell>
                      <TableCell>Success Rate</TableCell>
                      <TableCell>Avg Confidence</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analyticsData.sessions.map((session) => (
                      <TableRow key={session.id}>
                        <TableCell>
                          {new Date(session.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Chip label={session.sport} color="primary" size="small" />
                        </TableCell>
                        <TableCell>
                          {session.duration ? `${Math.round(session.duration / 60)}m` : '-'}
                        </TableCell>
                        <TableCell>{session.total_actions || 0}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <LinearProgress
                              variant="determinate"
                              value={session.total_actions ? ((session.successful_actions || 0) / session.total_actions * 100) : 0}
                              sx={{ width: 60, mr: 1 }}
                            />
                            {session.total_actions ? 
                              `${((session.successful_actions || 0) / session.total_actions * 100).toFixed(1)}%` : 
                              '0%'
                            }
                          </Box>
                        </TableCell>
                        <TableCell>
                          {session.average_confidence ? 
                            `${(session.average_confidence * 100).toFixed(1)}%` : 
                            '-'
                          }
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={session.is_active ? 'Active' : 'Completed'}
                            color={session.is_active ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => setDetailsDialog({ open: true, session })}
                          >
                            <Visibility />
                          </IconButton>
                          <IconButton size="small">
                            <Download />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </>
      ) : (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No analytics data available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Start tracking sessions to see your performance analytics
          </Typography>
        </Box>
      )}

      {/* Session Details Dialog */}
      <Dialog
        open={detailsDialog.open}
        onClose={() => setDetailsDialog({ open: false, session: null })}
        maxWidth="md"
        fullWidth
      >
        {detailsDialog.session && (
          <>
            <DialogTitle>
              Session Details - {detailsDialog.session.name}
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Sport
                  </Typography>
                  <Typography variant="body1">
                    {detailsDialog.session.sport}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {new Date(detailsDialog.session.created_at).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Actions
                  </Typography>
                  <Typography variant="body1">
                    {detailsDialog.session.total_actions || 0}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Successful Actions
                  </Typography>
                  <Typography variant="body1">
                    {detailsDialog.session.successful_actions || 0}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Description
                  </Typography>
                  <Typography variant="body1">
                    {detailsDialog.session.description || 'No description provided'}
                  </Typography>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailsDialog({ open: false, session: null })}>
                Close
              </Button>
              <Button variant="contained" startIcon={<Download />}>
                Export Session
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default Analytics;
