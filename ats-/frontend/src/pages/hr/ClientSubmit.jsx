import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BuildingOfficeIcon, 
  UserIcon, 
  EnvelopeIcon,
  PlusIcon,
  CheckIcon,
  XMarkIcon,
  DocumentTextIcon,
  CalendarIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import api from '../../utils/api';
import { useClients } from '../../store/clients';

const ClientSubmit = () => {
  const { addClient, clients } = useClients();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    total_clients: 0,
    total_resumes: 0,
    shortlisted: 0,
    interviews: 0,
    offers: 0
  });
  const [loadingStats, setLoadingStats] = useState(true);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      const response = await api.post('/api/hr/clients', formData);
      console.log('Client created successfully:', response.data);
      addClient(response.data); // Add to context
      setSuccess(true);
      setFormData({ name: '', email: '', company: '' });
    } catch (error) {
      console.error('Error creating client:', error);
      setError(error.response?.data?.detail || error.response?.data?.message || 'Failed to create client');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setSuccess(false);
    setError('');
    setFormData({ name: '', email: '', company: '' });
  };

  useEffect(() => {
    fetchStats();
  }, [clients]);

  const fetchStats = async () => {
    try {
      setLoadingStats(true);
      const response = await api.get('/api/stats/hr-dashboard');
      const data = response.data;
      
      // Transform HR dashboard data to match ClientSubmit card requirements
      const transformedStats = {
        total_clients: clients.length, // Use clients from store
        total_resumes: data.total_resumes || 0,
        interviews: data.status_breakdown?.interview || 0,
        offers: (data.status_breakdown?.select || 0) + (data.status_breakdown?.offer_letter || 0)
      };
      
      setStats(transformedStats);
    } catch (error) {
      console.error('Error fetching stats:', error);
      // Set default values on error
      setStats({
        total_clients: clients.length,
        total_resumes: 0,
        interviews: 0,
        offers: 0
      });
    } finally {
      setLoadingStats(false);
    }
  };

  return (
    <div className="p-6">
      <Header 
        title="Client Submit" 
        subtitle="Add new clients to the system"
      />

      {/* Statistics Cards */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Clients</p>
              <p className="text-2xl font-bold text-gray-900">
                {loadingStats ? '...' : stats.total_clients}
              </p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <BuildingOfficeIcon className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Resumes Obtained</p>
              <p className="text-2xl font-bold text-gray-900">
                {loadingStats ? '...' : stats.total_resumes}
              </p>
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
              <p className="text-2xl font-bold text-blue-600">
                {loadingStats ? '...' : stats.interviews}
              </p>
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
              <p className="text-2xl font-bold text-green-600">
                {loadingStats ? '...' : stats.offers}
              </p>
            </div>
            <div className="p-3 rounded-full bg-green-100">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm p-8"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Client Creation Form */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <PlusIcon className="w-6 h-6 mr-2 text-blue-600" />
                Add New Client
              </h2>

              {/* Success Message */}
              {success && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mb-6 bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded-lg flex items-center"
                >
                  <CheckIcon className="h-5 w-5 mr-2" />
                  Client created successfully!
                </motion.div>
              )}

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg flex items-center"
                >
                  <XMarkIcon className="h-5 w-5 mr-2" />
                  {error}
                </motion.div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
            {/* Client Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Client Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="name"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  placeholder="Enter client name"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  id="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  placeholder="Enter email address"
                />
              </div>
            </div>

            {/* Company */}
            <div>
              <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                Company Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <BuildingOfficeIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="company"
                  name="company"
                  required
                  value={formData.company}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  placeholder="Enter company name"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 btn-gradient-primary py-3 px-6 rounded-lg font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <div className="spinner w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-3"></div>
                    Creating Client...
                  </>
                ) : (
                  <>
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Add Client
                  </>
                )}
              </button>

              {(success || error) && (
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Add Another
                </button>
              )}
            </div>
              </form>
            </div>

            {/* Client List Sidebar */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <UserIcon className="w-6 h-6 mr-2 text-blue-600" />
                Existing Clients
                <span className="ml-2 bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                  {clients.length}
                </span>
              </h2>

              {clients.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {clients.map((client) => (
                    <div
                      key={client.id}
                      className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {client.name}
                          </h4>
                          <p className="text-xs text-gray-500 truncate">
                            {client.email}
                          </p>
                          <p className="text-xs text-gray-400 truncate">
                            {client.company}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BuildingOfficeIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No clients created yet</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Create your first client using the form
                  </p>
                </div>
              )}

              {/* Info Card */}
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <BuildingOfficeIcon className="h-5 w-5 text-blue-600 mt-0.5" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">Client Information</h3>
                    <p className="mt-1 text-sm text-blue-700">
                      Clients will be automatically created in the system after successful submission. 
                      You can manage clients through the admin panel.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ClientSubmit;
