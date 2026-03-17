import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  BuildingOfficeIcon,
  UserIcon,
  DocumentTextIcon,
  CalendarIcon,
  ChartBarIcon,
  EyeIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import { useClients } from '../../store/clients';
import api from '../../utils/api';

const ClientDashboard = () => {
  const navigate = useNavigate();
  const { clients, loading } = useClients();
  const [clientStats, setClientStats] = useState({});
  const [loadingStats, setLoadingStats] = useState(true);
  const [summaryStats, setSummaryStats] = useState({
    total_clients: 0,
    total_resumes: 0,
    shortlisted: 0,
    interviews: 0,
    offers: 0
  });

  useEffect(() => {
    fetchClientStats();
  }, [clients]);

  const fetchClientStats = async () => {
    if (!clients || clients.length === 0) {
      setClientStats({});
      setSummaryStats({
        total_clients: 0,
        total_resumes: 0,
        shortlisted: 0,
        interviews: 0,
        offers: 0
      });
      setLoadingStats(false);
      return;
    }

    try {
      setLoadingStats(true);
      const response = await api.get('/api/hr/clients/bulk-stats');
      const stats = response.data?.client_stats || {};
      const summary = response.data?.summary || {};

      setClientStats(stats);
      setSummaryStats({
        total_clients: summary.total_clients ?? clients.length,
        total_resumes: summary.total_resumes ?? 0,
        shortlisted: summary.shortlisted ?? 0,
        interviews: summary.interviews ?? 0,
        offers: summary.offers ?? 0
      });
    } catch (error) {
      console.error('Error fetching client stats:', error);
      setClientStats({});
      setSummaryStats({
        total_clients: clients.length,
        total_resumes: 0,
        shortlisted: 0,
        interviews: 0,
        offers: 0
      });
    } finally {
      setLoadingStats(false);
    }
  };


  const ClientCard = ({ client }) => {
    const stats = clientStats[client.id] || {
      total_resumes: 0,
      shortlisted: 0,
      interviews: 0,
      offers: 0
    };

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
      >
        {/* Client Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <BuildingOfficeIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{client.name}</h3>
              <p className="text-sm text-gray-500">{client.company}</p>
              <p className="text-xs text-gray-400">{client.email}</p>
            </div>
          </div>
          <button
            onClick={() => navigate(`/hr/clients/${client.id}`)}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
            title="View Client Details"
          >
            <EyeIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Total Resumes</p>
                <p className="text-lg font-bold text-gray-900">{stats.total_resumes}</p>
              </div>
              <DocumentTextIcon className="w-5 h-5 text-gray-400" />
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Shortlisted</p>
                <p className="text-lg font-bold text-yellow-600">{stats.shortlisted}</p>
              </div>
              <UserIcon className="w-5 h-5 text-yellow-400" />
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Interviews</p>
                <p className="text-lg font-bold text-blue-600">{stats.interviews}</p>
              </div>
              <CalendarIcon className="w-5 h-5 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Offers</p>
                <p className="text-lg font-bold text-green-600">{stats.offers}</p>
              </div>
              <ChartBarIcon className="w-5 h-5 text-green-400" />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex space-x-3">
            <button
              onClick={() => navigate(`/hr/clients/${client.id}`)}
              className="flex-1 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition-colors"
            >
              View Details
            </button>
            <button
              onClick={() => {
                // TODO: Implement share resume functionality
                alert('Share resume functionality coming soon!');
              }}
              className="flex-1 px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              Share Resume
            </button>
          </div>
        </div>
      </motion.div>
    );
  };

  if (loading || loadingStats) {
    return (
      <div className="p-6">
        <Header title="Client Dashboard" subtitle="Overview of all clients and their statistics" />
        <div className="mt-6 flex justify-center">
          <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header
        title="Client Dashboard"
        subtitle="Overview of all clients and their statistics"
      />

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Clients</p>
              <p className="text-2xl font-bold text-gray-900">{summaryStats.total_clients ?? clients.length}</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <BuildingOfficeIcon className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Resumes</p>
              <p className="text-2xl font-bold text-gray-900">{summaryStats.total_resumes}</p>
            </div>
            <div className="p-3 rounded-full bg-gray-100">
              <DocumentTextIcon className="h-6 w-6 text-gray-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Interviews Scheduled</p>
              <p className="text-2xl font-bold text-blue-600">{summaryStats.interviews}</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <CalendarIcon className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Selected</p>
              <p className="text-2xl font-bold text-green-600">{summaryStats.offers}</p>
            </div>
            <div className="p-3 rounded-full bg-green-100">
              <ChartBarIcon className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Client Cards */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Client Overview</h2>
          <button
            onClick={() => navigate('/hr/client-submit')}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Add Client</span>
          </button>
        </div>

        {clients.length === 0 ? (
          <div className="text-center py-12">
            <BuildingOfficeIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No clients yet</h3>
            <p className="text-gray-500 mb-6">Create your first client to get started</p>
            <button
              onClick={() => navigate('/hr/client-submit')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
            >
              Create Client
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {clients.map((client, index) => (
              <motion.div
                key={client.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <ClientCard client={client} />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientDashboard;



