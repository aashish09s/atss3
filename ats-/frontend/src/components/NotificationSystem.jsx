import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon,
  BellIcon
} from '@heroicons/react/24/outline';
import { getWebSocketUrl } from '../utils/api';

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);
  const [ws, setWs] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    let websocket = null;
    let reconnectTimeout = null;
    let isManualClose = false;

    const connectWebSocket = () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setConnectionStatus('no_token');
        return;
      }

      try {
        // Get WebSocket URL from API configuration
        const wsUrl = getWebSocketUrl(`/ws/resume-sync?token=${token}`);
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
          console.log('WebSocket connected for notifications');
          setWs(websocket);
          setConnectionStatus('connected');
          // Set global connection status
          window.wsConnectionStatus = 'connected';
          // Clear any pending reconnect
          if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
          }
        };

        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            if (data.type === 'notification') {
              addNotification(data.notification);
            } else if (data.type === 'resume_update') {
              addNotification({
                title: 'Resume Update',
                message: `Resume ${data.action}`,
                type: 'info'
              });
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        websocket.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          setWs(null);
          setConnectionStatus('disconnected');
          window.wsConnectionStatus = 'disconnected';
          
          // Handle specific close codes
          if (event.code === 4001) {
            console.log('WebSocket closed due to expired token');
            // Token expired - try to refresh or redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            // Don't attempt to reconnect with invalid token
            return;
          }
          
          // Reconnect only if not manually closed and token exists
          if (!isManualClose && localStorage.getItem('access_token')) {
            console.log('Attempting to reconnect WebSocket in 3 seconds...');
            reconnectTimeout = setTimeout(() => {
              connectWebSocket();
            }, 3000);
          }
        };

        websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('error');
          window.wsConnectionStatus = 'error';
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setConnectionStatus('error');
      }
    };

    // Initial connection
    connectWebSocket();

    return () => {
      isManualClose = true;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  const addNotification = (notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      ...notification,
      timestamp: new Date()
    };

    setNotifications(prev => [newNotification, ...prev].slice(0, 5)); // Keep only 5 notifications

    // Auto-remove after 5 seconds for success/info notifications
    if (notification.type === 'success' || notification.type === 'info') {
      setTimeout(() => {
        removeNotification(id);
      }, 5000);
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'info':
      default:
        return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBackgroundColor = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getTextColor = (type) => {
    switch (type) {
      case 'success':
        return 'text-green-800';
      case 'error':
        return 'text-red-800';
      case 'warning':
        return 'text-yellow-800';
      case 'info':
      default:
        return 'text-blue-800';
    }
  };

  // Expose method to add notifications globally
  useEffect(() => {
    window.addNotification = addNotification;
    return () => {
      delete window.addNotification;
    };
  }, []);

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      <AnimatePresence>
        {notifications.map((notification) => (
          <motion.div
            key={notification.id}
            initial={{ opacity: 0, x: 300, scale: 0.8 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 300, scale: 0.8 }}
            className={`max-w-sm w-full ${getBackgroundColor(notification.type)} border rounded-lg shadow-lg p-4`}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {getIcon(notification.type)}
              </div>
              <div className="ml-3 flex-1">
                <div className={`text-sm font-medium ${getTextColor(notification.type)}`}>
                  {notification.title}
                </div>
                {notification.message && (
                  <div className={`mt-1 text-sm ${getTextColor(notification.type)} opacity-80`}>
                    {notification.message}
                  </div>
                )}
                {notification.timestamp && (
                  <div className="mt-1 text-xs text-gray-500">
                    {notification.timestamp.toLocaleTimeString()}
                  </div>
                )}
              </div>
              <div className="flex-shrink-0 ml-4">
                <button
                  onClick={() => removeNotification(notification.id)}
                  className={`inline-flex ${getTextColor(notification.type)} hover:opacity-70 focus:outline-none`}
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// Utility function to show notifications from anywhere in the app
export const showNotification = (title, message, type = 'info') => {
  if (window.addNotification) {
    window.addNotification({ title, message, type });
  }
};

// WebSocket notification helper - uses the global connection status
export const useWebSocketNotifications = () => {
  // Return connection status from global state if available
  // This prevents creating multiple WebSocket connections
  return window.wsConnectionStatus || 'disconnected';
};

// Connection status indicator component
export const ConnectionStatus = () => {
  const status = useWebSocketNotifications();

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'disconnected':
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'connected':
        return 'Real-time updates active';
      case 'error':
        return 'Connection error';
      case 'disconnected':
      default:
        return 'Offline';
    }
  };

  return (
    <div className="flex items-center space-x-2 text-sm text-gray-600">
      <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`}></div>
      <span>{getStatusText(status)}</span>
    </div>
  );
};

export default NotificationSystem;
