import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import {
  DocumentCheckIcon,
  UsersIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState([]);
  const [recentActions, setRecentActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/stats/manager-dashboard');
      const data = response.data;
      
      // Transform backend data to match our stats format
      const transformedStats = [
        {
          name: 'Shared Resumes',
          value: data.shared_resumes || '0',
          change: data.shared_resumes > 0 ? `+${data.shared_resumes}` : '0',
          changeType: data.shared_resumes > 0 ? 'increase' : 'neutral',
          icon: DocumentCheckIcon,
          color: 'bg-blue-500',
        },
        {
          name: 'Approved',
          value: data.approved || '0',
          change: data.approved > 0 ? `+${data.approved}` : '0',
          changeType: data.approved > 0 ? 'increase' : 'neutral',
          icon: CheckCircleIcon,
          color: 'bg-green-500',
        },
        {
          name: 'Pending Review',
          value: data.pending_review || '0',
          change: '0',
          changeType: 'neutral',
          icon: ClockIcon,
          color: 'bg-yellow-500',
        },
        {
          name: 'Interviews',
          value: data.interviews_scheduled || '0',
          change: data.interviews_scheduled > 0 ? `+${data.interviews_scheduled}` : '0',
          changeType: data.interviews_scheduled > 0 ? 'increase' : 'neutral',
          icon: UsersIcon,
          color: 'bg-purple-500',
        },
      ];

      // Transform recent actions data
      const transformedActions = data.recent_shared?.map((resume, index) => ({
        id: index + 1,
        action: resume.status === 'select' ? 'Approved' : 
                resume.status === 'reject' ? 'Rejected' : 
                resume.status === 'interview' ? 'Interview Scheduled' : 'Status Updated',
        candidate: resume.candidate_name || 'Unknown',
        time: formatTimeAgo(resume.shared_at),
        status: resume.status,
      })) || [];

      setStats(transformedStats);
      setRecentActions(transformedActions);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
      // Set default empty data
      setStats([]);
      setRecentActions([]);
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

  const handleQuickAction = (action) => {
    switch (action) {
      case 'review':
        navigate('/manager/shared-resumes');
        break;
      case 'interviews':
        navigate('/manager/shared-resumes');
        break;
      case 'offers':
        navigate('/manager/shared-resumes');
        break;
      default:
        break;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'select': return 'text-green-600 bg-green-100';
      case 'reject': return 'text-red-600 bg-red-100';
      case 'interview': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header 
          title="Manager Dashboard" 
          subtitle="Review shared resumes and manage hiring decisions"
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
          title="Manager Dashboard" 
          subtitle="Review shared resumes and manage hiring decisions"
        />
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header 
        title="Manager Dashboard" 
        subtitle="Review shared resumes and manage hiring decisions"
      />

      <div className="mt-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-xl shadow-sm p-6 card-hover"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  <p className={`text-sm mt-2 ${
                    stat.changeType === 'increase' ? 'text-green-600' : 
                    stat.changeType === 'decrease' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {stat.change} from last week
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl shadow-sm"
          >
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Actions</h3>
            </div>
            <div className="p-6">
              {recentActions.length > 0 ? (
                <div className="space-y-4">
                  {recentActions.map((action) => (
                    <div key={action.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                      <div className="flex items-center space-x-4">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(action.status)}`}>
                              {action.action}
                            </span>
                            <span className="ml-2">{action.candidate}</span>
                          </p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500">{action.time}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No recent actions</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button 
                onClick={() => handleQuickAction('review')}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all cursor-pointer"
              >
                <DocumentCheckIcon className="h-6 w-6 text-blue-500 mb-2" />
                <h4 className="font-medium text-gray-900">Review Shared Resumes</h4>
                <p className="text-sm text-gray-600">View and approve/reject candidate profiles</p>
              </button>
              
              <button 
                onClick={() => handleQuickAction('interviews')}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-all cursor-pointer"
              >
                <UsersIcon className="h-6 w-6 text-green-500 mb-2" />
                <h4 className="font-medium text-gray-900">Schedule Interviews</h4>
                <p className="text-sm text-gray-600">Set up interviews with approved candidates</p>
              </button>
              
              <button 
                onClick={() => handleQuickAction('offers')}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-all cursor-pointer"
              >
                <CheckCircleIcon className="h-6 w-6 text-purple-500 mb-2" />
                <h4 className="font-medium text-gray-900">Generate Offers</h4>
                <p className="text-sm text-gray-600">Create offer letters for selected candidates</p>
              </button>
            </div>
          </motion.div>
        </div>

        {/* Pending Reviews Alert */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Pending Reviews</h3>
              <p className="text-blue-100">
                You have {stats.find(s => s.name === 'Pending Review')?.value || 0} resume{stats.find(s => s.name === 'Pending Review')?.value !== 1 ? 's' : ''} waiting for your review
              </p>
            </div>
            <button 
              onClick={() => handleQuickAction('review')}
              className="bg-white text-blue-600 px-6 py-2 rounded-lg font-medium hover:bg-blue-50 transition-colors cursor-pointer"
            >
              Review Now
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
