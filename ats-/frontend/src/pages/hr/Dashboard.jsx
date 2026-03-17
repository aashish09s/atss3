import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import {
  DocumentArrowUpIcon,
  UsersIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  BriefcaseIcon,
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/stats/hr-dashboard');
      const data = response.data;
      
      // Transform backend data to match our stats format
      const transformedStats = [
        {
          name: 'Active Requirements',
          value: data.active_jds || '0',
          change: data.active_jds > 0 ? `${data.active_jds} active` : '0 active',
          changeType: data.active_jds > 0 ? 'increase' : 'neutral',
          icon: BriefcaseIcon,
          color: 'bg-green-500',
        },
        {
          name: 'New Resumes',
          value: data.resumes_this_week || '0',
          change: data.resumes_this_week > 0 ? `+${data.resumes_this_week}` : '0',
          changeType: data.resumes_this_week > 0 ? 'increase' : 'neutral',
          icon: DocumentArrowUpIcon,
          color: 'bg-blue-500',
        },
        {
          name: 'Shortlisted',
          value: data.status_breakdown?.shortlisting || '0',
          change: data.status_breakdown?.shortlisting > 0 ? `+${data.status_breakdown.shortlisting}` : '0',
          changeType: data.status_breakdown?.shortlisting > 0 ? 'increase' : 'neutral',
          icon: UsersIcon,
          color: 'bg-purple-500',
        },
        {
          name: 'ATS Score Avg',
          value: `${data.ats_statistics?.average_score || 0}%`,
          change: data.ats_statistics?.average_score > 0 ? `+${data.ats_statistics.average_score}%` : '0%',
          changeType: data.ats_statistics?.average_score > 0 ? 'increase' : 'neutral',
          icon: ChartBarIcon,
          color: 'bg-orange-500',
        },
      ];

      // Transform recent activity data - store raw timestamp, format during render
      const transformedActivity = data.recent_uploads?.map((upload, index) => ({
        id: index + 1,
        action: 'Resume uploaded',
        candidate: upload.candidate_name || 'Unknown',
        timestamp: upload.created_at, // Store raw timestamp
        status: upload.status,
      })) || [];

      setStats(transformedStats);
      setRecentActivity(transformedActivity);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
      // Set default empty data
      setStats([]);
      setRecentActivity([]);
    } finally {
      setLoading(false);
    }
  };

  // Show relative time only: "just now", "1m ago", "3m ago", "10m ago", "45m ago", "59m ago", "1 hour ago", "5 hours ago", "2 days ago", etc.
  const formatExactTime = (dateString) => {
    if (!dateString) return 'Unknown time';

    const parseDate = (s) => {
      if (!s) return null;
      const str = String(s).trim();

      // Numeric epoch (seconds or ms)
      if (/^\d+$/.test(str)) {
        const n = Number(str);
        return n > 1e12 ? new Date(n) : new Date(n * 1000);
      }

      // ISO with timezone (Z or offset) -> parse directly
      if (/Z$/i.test(str) || /[+\-]\d{2}:?\d{2}$/.test(str)) {
        return new Date(str);
      }

      // ISO-like without timezone (backend sends UTC without Z): "2025-11-05T07:22:53.123456"
      // Backend uses datetime.utcnow() so treat as UTC by appending Z
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(str)) {
        return new Date(str + 'Z'); // Force UTC parsing
      }

      // Common DB format "YYYY-MM-DD HH:MM:SS" -> treat as UTC
      if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(str)) {
        return new Date(str.replace(' ', 'T') + 'Z');
      }

      // Fallback
      return new Date(str);
    };

    const date = parseDate(dateString);
    if (!date || isNaN(date)) return 'Unknown time';

    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);

    if (diffSeconds < 60) return 'just now';

    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;

    const diffDays = Math.floor(diffHours / 24);
    return diffDays === 1 ? '1 day ago' : `${diffDays} days ago`;
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'upload':
        navigate('/hr/upload');
        break;
      case 'candidates':
        navigate('/hr/parsed-profiles');
        break;
      case 'ats':
        navigate('/hr/resumes');
        break;
      default:
        break;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header 
          title="HR Dashboard" 
          subtitle=" Manage Resumes, Candidates, and Hiring Process"
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
          title="HR Dashboard" 
          subtitle="Manage resumes, candidates, and hiring process"
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
        title="HR Dashboard" 
        subtitle="Manage resumes, candidates, and hiring process"
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

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-xl shadow-sm"
        >
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            {recentActivity.length > 0 ? (
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                    <div className="flex items-center space-x-4">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {activity.action}: <span className="text-blue-600">{activity.candidate}</span>
                        </p>
                        {activity.status && (
                          <p className="text-xs text-gray-500 mt-1">
                            Status: <span className="capitalize">{activity.status}</span>
                          </p>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-500">{formatExactTime(activity.timestamp)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No recent activity</p>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => handleQuickAction('upload')}
              className="p-4 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all cursor-pointer"
            >
              <DocumentArrowUpIcon className="h-8 w-8 text-blue-500 mb-2" />
              <h4 className="font-medium text-gray-900">Upload Resume</h4>
              <p className="text-sm text-gray-600">Add new candidate resume</p>
            </button>
            <button 
              onClick={() => handleQuickAction('candidates')}
              className="p-4 text-left border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-all cursor-pointer"
            >
              <UsersIcon className="h-8 w-8 text-green-500 mb-2" />
              <h4 className="font-medium text-gray-900">View Candidates</h4>
              <p className="text-sm text-gray-600">Browse parsed profiles</p>
            </button>
            <button 
              onClick={() => handleQuickAction('ats')}
              className="p-4 text-left border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-all cursor-pointer"
            >
              <ChartBarIcon className="h-8 w-8 text-purple-500 mb-2" />
              <h4 className="font-medium text-gray-900">ATS Scoring</h4>
              <p className="text-sm text-gray-600">Analyze resume quality</p>
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
