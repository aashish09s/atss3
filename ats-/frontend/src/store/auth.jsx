import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import api from '../utils/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSessionWarning, setShowSessionWarning] = useState(false);
  const [sessionTimeLeft, setSessionTimeLeft] = useState(0);
  
  // Session management refs
  const inactivityTimer = useRef(null);
  const warningTimer = useRef(null);
  const countdownInterval = useRef(null);
  const lastActivity = useRef(Date.now());
  const INACTIVITY_TIMEOUT = 10 * 60 * 1000; // 10 minutes in milliseconds
  const WARNING_TIME = 2 * 60 * 1000; // Show warning 2 minutes before logout

  // Activity tracking functions
  const resetInactivityTimer = () => {
    lastActivity.current = Date.now();
    
    // Clear existing timers
    if (inactivityTimer.current) {
      clearTimeout(inactivityTimer.current);
    }
    if (warningTimer.current) {
      clearTimeout(warningTimer.current);
    }
    if (countdownInterval.current) {
      clearInterval(countdownInterval.current);
    }
    
    // Hide warning if it was showing
    setShowSessionWarning(false);
    setSessionTimeLeft(0);
    
    // Set new warning timer (8 minutes from now)
    warningTimer.current = setTimeout(() => {
      setShowSessionWarning(true);
      setSessionTimeLeft(120); // 2 minutes left
      
      // Start countdown
      countdownInterval.current = setInterval(() => {
        setSessionTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(countdownInterval.current);
            handleAutoLogout();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
    }, INACTIVITY_TIMEOUT - WARNING_TIME);
    
    // Set new logout timer (10 minutes from now)
    inactivityTimer.current = setTimeout(() => {
      handleAutoLogout();
    }, INACTIVITY_TIMEOUT);
  };

  const handleAutoLogout = () => {
    console.log('Auto-logout due to inactivity');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setShowSessionWarning(false);
    window.location.href = '/login';
  };

  const extendSession = () => {
    console.log('Session extended by user activity');
    // Hide the warning modal if it's showing
    setShowSessionWarning(false);
    setSessionTimeLeft(0);
    resetInactivityTimer();
  };

  const handleUserActivity = () => {
    // Only reset timer if user is authenticated and warning modal is not showing
    if (user && !showSessionWarning) {
      extendSession();
    }
  };

  // Handle explicit session extension from modal
  const handleExtendSession = () => {
    console.log('Session extended by user clicking "Stay Logged In"');
    setShowSessionWarning(false);
    setSessionTimeLeft(0);
    resetInactivityTimer();
  };

  // Set up activity listeners
  useEffect(() => {
    if (user) {
      // Add event listeners for user activity
      const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
      
      events.forEach(event => {
        document.addEventListener(event, handleUserActivity, true);
      });
      
      // Start the inactivity timer
      resetInactivityTimer();
      
      return () => {
        // Cleanup event listeners
        events.forEach(event => {
          document.removeEventListener(event, handleUserActivity, true);
        });
        
        // Clear timers
        if (inactivityTimer.current) {
          clearTimeout(inactivityTimer.current);
        }
        if (warningTimer.current) {
          clearTimeout(warningTimer.current);
        }
        if (countdownInterval.current) {
          clearInterval(countdownInterval.current);
        }
      };
    }
  }, [user]);

  useEffect(() => {
    // Check for stored user data on mount
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('access_token');
    
    console.log('Auth context initializing...');
    console.log('Stored user:', storedUser);
    console.log('Stored token:', storedToken ? 'exists' : 'missing');
    
    if (storedUser && storedToken) {
      try {
        const userData = JSON.parse(storedUser);
        console.log('Setting user from storage:', userData);
        setUser(userData);
        
        // Verify the user state was set
        setTimeout(() => {
          console.log('User state after initialization:', userData);
          console.log('isAuthenticated should be:', !!userData);
        }, 50);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        // Clear corrupted data
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      console.log('Attempting login for:', email);
      const response = await api.post('/api/auth/issue-tokens', {
        email,
        password,
      });

      console.log('Login response:', response.data);
      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens and user data
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(userData));

      console.log('Stored user data:', userData);
      console.log('Setting user state...');
      setUser(userData);
      
      // Verify the user state was set
      setTimeout(() => {
        console.log('User state after login:', userData);
        console.log('isAuthenticated should be:', !!userData);
      }, 50);

      return { success: true, user: userData };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  };

  const logout = () => {
    // Clear timers
    if (inactivityTimer.current) {
      clearTimeout(inactivityTimer.current);
    }
    if (warningTimer.current) {
      clearTimeout(warningTimer.current);
    }
    if (countdownInterval.current) {
      clearInterval(countdownInterval.current);
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setShowSessionWarning(false);
  };

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
    showSessionWarning,
    sessionTimeLeft,
    extendSession: handleExtendSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
