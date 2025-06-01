import React, { createContext, useContext, useReducer, useEffect } from 'react';

const SessionContext = createContext();

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

// Session state management
const initialState = {
  currentSession: null,
  sessions: [],
  isTracking: false,
  selectedSport: 'basketball',
  settings: {
    feedbackTypes: ['audio', 'visual'],
    sensitivity: 0.7,
    minConfidence: 0.8,
    cameraSource: 0
  },
  stats: {
    totalActions: 0,
    successfulActions: 0,
    successRate: 0,
    averageScore: 0
  },
  loading: false,
  error: null
};

const sessionReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload, loading: false };
    
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSession: action.payload };
    
    case 'CREATE_SESSION':
      return {
        ...state,
        currentSession: action.payload,
        sessions: [action.payload, ...state.sessions]
      };
    
    case 'UPDATE_SESSION':
      const updatedSessions = state.sessions.map(session =>
        session.id === action.payload.id ? action.payload : session
      );
      return {
        ...state,
        sessions: updatedSessions,
        currentSession: state.currentSession?.id === action.payload.id ? action.payload : state.currentSession
      };
    
    case 'SET_TRACKING':
      return { ...state, isTracking: action.payload };
    
    case 'SET_SELECTED_SPORT':
      return { ...state, selectedSport: action.payload };
    
    case 'UPDATE_SETTINGS':
      return {
        ...state,
        settings: { ...state.settings, ...action.payload }
      };
    
    case 'UPDATE_STATS':
      return {
        ...state,
        stats: { ...state.stats, ...action.payload }
      };
    
    case 'RESET_STATS':
      return {
        ...state,
        stats: initialState.stats
      };
    
    default:
      return state;
  }
};

export const SessionProvider = ({ children }) => {
  const [state, dispatch] = useReducer(sessionReducer, initialState);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // API Functions
  const createSession = async (sessionData) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const response = await fetch(`${API_BASE}/api/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sessionData),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const session = await response.json();
      dispatch({ type: 'CREATE_SESSION', payload: session });
      return session;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const getSessions = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const response = await fetch(`${API_BASE}/api/sessions`);
      if (!response.ok) {
        throw new Error('Failed to fetch sessions');
      }
      
      const sessions = await response.json();
      dispatch({ type: 'SET_SESSIONS', payload: sessions });
      return sessions;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const getSession = async (sessionId) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch session');
      }
      
      const session = await response.json();
      dispatch({ type: 'SET_CURRENT_SESSION', payload: session });
      return session;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const startTracking = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/tracking/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sport: state.selectedSport,
          settings: state.settings
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to start tracking');
      }
      
      dispatch({ type: 'SET_TRACKING', payload: true });
      return true;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const stopTracking = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/tracking/stop`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to stop tracking');
      }
      
      dispatch({ type: 'SET_TRACKING', payload: false });
      return true;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const getAnalytics = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE}/api/analytics/session/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }
      
      const analytics = await response.json();
      return analytics;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const updateSettings = (newSettings) => {
    dispatch({ type: 'UPDATE_SETTINGS', payload: newSettings });
  };

  const setSelectedSport = (sport) => {
    dispatch({ type: 'SET_SELECTED_SPORT', payload: sport });
  };

  const updateStats = (stats) => {
    dispatch({ type: 'UPDATE_STATS', payload: stats });
  };

  const clearError = () => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  // Load sessions on mount
  useEffect(() => {
    getSessions().catch(console.error);
  }, []);

  const contextValue = {
    ...state,
    createSession,
    getSessions,
    getSession,
    startTracking,
    stopTracking,
    getAnalytics,
    updateSettings,
    setSelectedSport,
    updateStats,
    clearError
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};
