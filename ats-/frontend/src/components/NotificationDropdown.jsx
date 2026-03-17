import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BellIcon, 
  XMarkIcon,
  UserIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import api from '../utils/api';
import { useAuth } from '../store/auth';

const NotificationDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);
  const { user } = useAuth();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      fetchNotifications();
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Fetch notifications when component mounts or user changes
  useEffect(() => {
    if (user) {
      fetchNotifications();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const notificationsList = [];

      // Fetch pending account requests (for admins)
      if (user?.role === 'admin' || user?.role === 'superadmin') {
        try {
          const response = await api.get('/api/admin/account-requests');
          const pendingRequests = (response.data || []).filter(req => req.status === 'pending');
          pendingRequests.forEach(req => {
            notificationsList.push({
              id: `account-request-${req.id || req._id}`,
              type: 'account_request',
              title: 'New Account Request',
              message: `${req.full_name || req.name || req.email} requested ${req.requested_role || 'access'}`,
              timestamp: new Date(req.created_at || Date.now()),
              link: user.role === 'superadmin' ? '/superadmin/admins' : '/admin/users',
              unread: true
            });
          });
        } catch (error) {
          console.error('Error fetching account requests:', error);
        }
      }

      // Fetch shared resumes (for managers)
      if (user?.role === 'manager') {
        try {
          const response = await api.get('/api/manager/resumes/shared');
          const sharedResumes = response.data || [];
          sharedResumes.slice(0, 5).forEach(resume => {
            notificationsList.push({
              id: `shared-resume-${resume.id}`,
              type: 'shared_resume',
              title: 'New Resume Shared',
              message: `Resume shared: ${resume.parsed_data?.name || 'Unknown'}`,
              timestamp: new Date(resume.shared_at || resume.created_at),
              link: '/manager/shared-resumes',
              unread: true
            });
          });
        } catch (error) {
          console.error('Error fetching shared resumes:', error);
        }
      }

      // Fetch recent activity (resumes, JDs, etc.) - only for HR and Admin
      if (user?.role === 'hr' || user?.role === 'admin') {
        try {
          const statsResponse = await api.get(`/api/stats/hr-dashboard`);
          const recentUploads = statsResponse.data?.recent_uploads || [];
          recentUploads.slice(0, 3).forEach(upload => {
            notificationsList.push({
              id: `recent-upload-${upload.id}`,
              type: 'recent_activity',
              title: 'Resume Uploaded',
              message: `${upload.candidate_name || upload.filename || 'Resume'} uploaded`,
              timestamp: new Date(upload.created_at || Date.now()),
              link: '/hr/resumes',
              unread: false
            });
          });
        } catch (error) {
          console.error('Error fetching recent activity:', error);
        }
      }

      // Sort by timestamp (newest first)
      notificationsList.sort((a, b) => b.timestamp - a.timestamp);

      setNotifications(notificationsList);
      setUnreadCount(notificationsList.filter(n => n.unread).length);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, unread: false }
          : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const formatTimeAgo = (date) => {
    if (!date) return 'Unknown time';
    
    try {
      const dateObj = date instanceof Date ? date : new Date(date);
      const now = new Date();
      
      if (isNaN(dateObj.getTime())) {
        return 'Invalid Date';
      }
      
      // Calculate difference in milliseconds using getTime() for timezone-independent calculation
      const diffInMs = now.getTime() - dateObj.getTime();
      
      // Handle negative differences (future dates)
      if (diffInMs < 0) {
        return 'Just now';
      }
      
      const diffInSeconds = Math.floor(diffInMs / 1000);
      const diffInMinutes = Math.floor(diffInSeconds / 60);
      const diffInHours = Math.floor(diffInMinutes / 60);
      const diffInDays = Math.floor(diffInHours / 24);
      const diffInWeeks = Math.floor(diffInDays / 7);
      const diffInMonths = Math.floor(diffInDays / 30);
      const diffInYears = Math.floor(diffInDays / 365);
      
      if (diffInYears > 0) {
        return `${diffInYears} year${diffInYears > 1 ? 's' : ''} ago`;
      } else if (diffInMonths > 0) {
        return `${diffInMonths} month${diffInMonths > 1 ? 's' : ''} ago`;
      } else if (diffInWeeks > 0) {
        return `${diffInWeeks} week${diffInWeeks > 1 ? 's' : ''} ago`;
      } else if (diffInDays > 0) {
        return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
      } else if (diffInHours > 0) {
        return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
      } else if (diffInMinutes > 0) {
        return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
      } else if (diffInSeconds > 0) {
        return `${diffInSeconds} second${diffInSeconds > 1 ? 's' : ''} ago`;
      } else {
        return 'Just now';
      }
    } catch (error) {
      console.error('Error formatting time ago:', error);
      return 'Unknown time';
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'account_request':
        return <UserIcon className="w-5 h-5 text-blue-500" />;
      case 'shared_resume':
        return <DocumentTextIcon className="w-5 h-5 text-green-500" />;
      case 'recent_activity':
        return <CheckCircleIcon className="w-5 h-5 text-purple-500" />;
      default:
        return <BellIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
        aria-label="Notifications"
      >
        <BellIcon className="h-6 w-6" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
                {unreadCount > 0 && (
                  <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
                    {unreadCount} new
                  </span>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <XMarkIcon className="w-4 h-4 text-gray-500" />
                </button>
              </div>

              {/* Notifications List */}
              <div className="overflow-y-auto flex-1">
                {loading ? (
                  <div className="p-4 text-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="text-sm text-gray-500 mt-2">Loading...</p>
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="p-8 text-center">
                    <BellIcon className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No notifications</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {notifications.map((notification) => (
                      <motion.div
                        key={notification.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                          notification.unread ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => {
                          markAsRead(notification.id);
                          if (notification.link) {
                            window.location.href = notification.link;
                          }
                          setIsOpen(false);
                        }}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0 mt-0.5">
                            {getNotificationIcon(notification.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium ${
                              notification.unread ? 'text-gray-900' : 'text-gray-700'
                            }`}>
                              {notification.title}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              {formatTimeAgo(notification.timestamp)}
                            </p>
                          </div>
                          {notification.unread && (
                            <div className="flex-shrink-0">
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              {notifications.length > 0 && (
                <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
                  <button
                    onClick={() => {
                      setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
                      setUnreadCount(0);
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Mark all as read
                  </button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationDropdown;

