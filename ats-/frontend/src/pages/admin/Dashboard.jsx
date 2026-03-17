import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import { 
  UsersIcon, 
  BriefcaseIcon,
  ChartBarIcon,
  DocumentTextIcon,
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_users: 0,
    hr_users: 0,
    manager_users: 0,
    linked_hr_users: 0,
    total_resumes: 0,
    total_job_descriptions: 0,
    pending_account_requests: 0,
    recent_users: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/stats/admin-dashboard');
      setStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching admin dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Unknown time';
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      
      // Calculate difference in milliseconds
      const diffInMs = now.getTime() - date.getTime();
      
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

  const getRoleColor = (role) => {
    switch (role) {
      case 'hr':
        return 'bg-blue-100 text-blue-800';
      case 'manager':
        return 'bg-purple-100 text-purple-800';
      case 'accountant':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const statCards = [
    {
      title: 'Total Users',
      value: stats.total_users,
      icon: UsersIcon,
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
      onClick: () => navigate('/admin/users')
    },
    {
      title: 'HR Users',
      value: stats.hr_users,
      icon: UserGroupIcon,
      color: 'bg-green-500',
      textColor: 'text-green-600',
      onClick: () => navigate('/admin/users')
    },
    {
      title: 'Managers',
      value: stats.manager_users,
      icon: BriefcaseIcon,
      color: 'bg-purple-500',
      textColor: 'text-purple-600',
      onClick: () => navigate('/admin/users')
    },
    {
      title: 'Linked HR',
      value: stats.linked_hr_users,
      icon: CheckCircleIcon,
      color: 'bg-indigo-500',
      textColor: 'text-indigo-600',
      subtitle: `${stats.hr_users > 0 ? Math.round((stats.linked_hr_users / stats.hr_users) * 100) : 0}% of HR users`
    },
    {
      title: 'Total Resumes',
      value: stats.total_resumes,
      icon: DocumentTextIcon,
      color: 'bg-orange-500',
      textColor: 'text-orange-600',
      onClick: () => navigate('/hr/resumes')
    },
    {
      title: 'Job Descriptions',
      value: stats.total_job_descriptions,
      icon: BriefcaseIcon,
      color: 'bg-teal-500',
      textColor: 'text-teal-600',
      onClick: () => navigate('/hr/jd-manager')
    },
    {
      title: 'Pending Requests',
      value: stats.pending_account_requests,
      icon: ClockIcon,
      color: 'bg-yellow-500',
      textColor: 'text-yellow-600',
      subtitle: 'Account requests',
      onClick: () => navigate('/admin/users')
    }
  ];

  if (loading) {
    return (
      <div className="p-6">
        <Header 
          title="Admin Dashboard" 
          subtitle="Manage users, services, and system overview"
        />
        <div className="mt-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Header 
          title="Admin Dashboard" 
          subtitle="Manage users, services, and system overview"
        />
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        title="Admin Dashboard" 
        subtitle="Manage users, services, and system overview"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((card, index) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={card.onClick}
              className={`bg-white rounded-xl shadow-sm p-6 hover:shadow-lg transition-all ${card.onClick ? 'cursor-pointer' : ''}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 mb-1">{card.title}</p>
                  <p className={`text-3xl font-bold ${card.textColor} mb-1`}>
                    {card.value}
                  </p>
                  {card.subtitle && (
                    <p className="text-xs text-gray-500">{card.subtitle}</p>
                  )}
                </div>
                <div className={`${card.color} p-3 rounded-lg`}>
                  <card.icon className="h-8 w-8 text-white" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Users */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recent Users</h3>
              <button
                onClick={() => navigate('/admin/users')}
                className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                View All
                <ArrowRightIcon className="h-4 w-4" />
              </button>
            </div>
            {stats.recent_users && stats.recent_users.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_users.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`${getRoleColor(user.role)} px-3 py-1 rounded-full text-xs font-medium`}>
                        {user.role.toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{user.username}</p>
                        <p className="text-sm text-gray-600">{user.email}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">{formatTimeAgo(user.created_at)}</p>
                      {user.is_linked && (
                        <span className="inline-flex items-center gap-1 text-xs text-green-600 mt-1">
                          <CheckCircleIcon className="h-3 w-3" />
                          Linked
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <UsersIcon className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                <p>No recent users</p>
              </div>
            )}
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/admin/users')}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all flex items-center gap-3"
              >
                <UsersIcon className="h-6 w-6 text-blue-500" />
                <div>
                  <h4 className="font-medium text-gray-900">Manage Users</h4>
                  <p className="text-sm text-gray-600">Create and manage HR, Manager, and Accountant users</p>
                </div>
              </button>
              <button
                onClick={() => navigate('/admin/services')}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-all flex items-center gap-3"
              >
                <BriefcaseIcon className="h-6 w-6 text-green-500" />
                <div>
                  <h4 className="font-medium text-gray-900">Manage Services</h4>
                  <p className="text-sm text-gray-600">Add and configure business services for invoices</p>
                </div>
              </button>
              <button
                onClick={() => navigate('/hr/dashboard')}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-all flex items-center gap-3"
              >
                <ChartBarIcon className="h-6 w-6 text-purple-500" />
                <div>
                  <h4 className="font-medium text-gray-900">View HR Dashboard</h4>
                  <p className="text-sm text-gray-600">Access HR features and analytics</p>
                </div>
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;

