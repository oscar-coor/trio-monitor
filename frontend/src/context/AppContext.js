/**
 * Global application context for state management
 * Reduces prop drilling and provides centralized state
 */

import React, { createContext, useContext, useReducer, useEffect } from 'react';

// Initial state
const initialState = {
  dashboardData: null,
  connectionStatus: 'connecting',
  loading: true,
  error: null,
  lastUpdated: null,
  theme: 'light',
  userPreferences: {
    pollingInterval: 2000,
    showAlerts: true,
    compactView: false,
    autoRefresh: true
  },
  alerts: [],
  isOnline: navigator.onLine
};

// Action types
export const ActionTypes = {
  SET_DASHBOARD_DATA: 'SET_DASHBOARD_DATA',
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_LAST_UPDATED: 'SET_LAST_UPDATED',
  SET_THEME: 'SET_THEME',
  UPDATE_USER_PREFERENCES: 'UPDATE_USER_PREFERENCES',
  SET_ALERTS: 'SET_ALERTS',
  ADD_ALERT: 'ADD_ALERT',
  REMOVE_ALERT: 'REMOVE_ALERT',
  SET_ONLINE_STATUS: 'SET_ONLINE_STATUS',
  RESET_STATE: 'RESET_STATE'
};

// Reducer function
function appReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_DASHBOARD_DATA:
      return {
        ...state,
        dashboardData: action.payload,
        loading: false,
        error: null,
        lastUpdated: new Date()
      };

    case ActionTypes.SET_CONNECTION_STATUS:
      return {
        ...state,
        connectionStatus: action.payload
      };

    case ActionTypes.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };

    case ActionTypes.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false
      };

    case ActionTypes.SET_LAST_UPDATED:
      return {
        ...state,
        lastUpdated: action.payload
      };

    case ActionTypes.SET_THEME:
      return {
        ...state,
        theme: action.payload
      };

    case ActionTypes.UPDATE_USER_PREFERENCES:
      return {
        ...state,
        userPreferences: {
          ...state.userPreferences,
          ...action.payload
        }
      };

    case ActionTypes.SET_ALERTS:
      return {
        ...state,
        alerts: action.payload
      };

    case ActionTypes.ADD_ALERT:
      return {
        ...state,
        alerts: [...state.alerts, action.payload]
      };

    case ActionTypes.REMOVE_ALERT:
      return {
        ...state,
        alerts: state.alerts.filter(alert => alert.id !== action.payload)
      };

    case ActionTypes.SET_ONLINE_STATUS:
      return {
        ...state,
        isOnline: action.payload
      };

    case ActionTypes.RESET_STATE:
      return {
        ...initialState,
        userPreferences: state.userPreferences // Keep user preferences
      };

    default:
      console.warn(`Unhandled action type: ${action.type}`);
      return state;
  }
}

// Create context
const AppContext = createContext();

// Provider component
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Load user preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedPreferences = localStorage.getItem('trio-monitor-preferences');
      if (savedPreferences) {
        const preferences = JSON.parse(savedPreferences);
        dispatch({
          type: ActionTypes.UPDATE_USER_PREFERENCES,
          payload: preferences
        });
      }
    } catch (error) {
      console.error('Failed to load user preferences:', error);
    }
  }, []);

  // Save user preferences to localStorage when they change
  useEffect(() => {
    try {
      localStorage.setItem(
        'trio-monitor-preferences',
        JSON.stringify(state.userPreferences)
      );
    } catch (error) {
      console.error('Failed to save user preferences:', error);
    }
  }, [state.userPreferences]);

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => dispatch({
      type: ActionTypes.SET_ONLINE_STATUS,
      payload: true
    });

    const handleOffline = () => dispatch({
      type: ActionTypes.SET_ONLINE_STATUS,
      payload: false
    });

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Action creators for common operations
  const actions = {
    setDashboardData: (data) => dispatch({
      type: ActionTypes.SET_DASHBOARD_DATA,
      payload: data
    }),

    setConnectionStatus: (status) => dispatch({
      type: ActionTypes.SET_CONNECTION_STATUS,
      payload: status
    }),

    setLoading: (loading) => dispatch({
      type: ActionTypes.SET_LOADING,
      payload: loading
    }),

    setError: (error) => dispatch({
      type: ActionTypes.SET_ERROR,
      payload: error
    }),

    setTheme: (theme) => dispatch({
      type: ActionTypes.SET_THEME,
      payload: theme
    }),

    updateUserPreferences: (preferences) => dispatch({
      type: ActionTypes.UPDATE_USER_PREFERENCES,
      payload: preferences
    }),

    addAlert: (alert) => dispatch({
      type: ActionTypes.ADD_ALERT,
      payload: {
        ...alert,
        id: alert.id || Date.now().toString(),
        timestamp: alert.timestamp || new Date()
      }
    }),

    removeAlert: (alertId) => dispatch({
      type: ActionTypes.REMOVE_ALERT,
      payload: alertId
    }),

    resetState: () => dispatch({
      type: ActionTypes.RESET_STATE
    })
  };

  const contextValue = {
    state,
    dispatch,
    actions
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook for using the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  
  return context;
};

// Selector hooks for specific state slices
export const useDashboardData = () => {
  const { state } = useAppContext();
  return state.dashboardData;
};

export const useConnectionStatus = () => {
  const { state } = useAppContext();
  return state.connectionStatus;
};

export const useUserPreferences = () => {
  const { state, actions } = useAppContext();
  return {
    preferences: state.userPreferences,
    updatePreferences: actions.updateUserPreferences
  };
};

export const useTheme = () => {
  const { state, actions } = useAppContext();
  return {
    theme: state.theme,
    setTheme: actions.setTheme
  };
};

export const useAlerts = () => {
  const { state, actions } = useAppContext();
  return {
    alerts: state.alerts,
    addAlert: actions.addAlert,
    removeAlert: actions.removeAlert
  };
};

export default AppContext;
