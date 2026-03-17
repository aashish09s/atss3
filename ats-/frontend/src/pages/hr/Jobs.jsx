import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import { BriefcaseIcon, PlusIcon, FunnelIcon, XMarkIcon, CalendarIcon, TrashIcon } from '@heroicons/react/24/outline';
import api from '../../utils/api';

const Jobs = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'active', 'inactive'
  const [clientFilter, setClientFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/hr/jds/');
      setJobs(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching jobs:', err);
      setError('Failed to load jobs');
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  // Get unique client names for filter dropdown
  const uniqueClients = useMemo(() => {
    const clients = jobs
      .map(job => job.client_name)
      .filter(name => name && name.trim() !== '')
      .filter((value, index, self) => self.indexOf(value) === index)
      .sort();
    return clients;
  }, [jobs]);

  // Filter jobs based on all filter criteria
  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      // Status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'active' && !job.is_active) return false;
        if (statusFilter === 'inactive' && job.is_active) return false;
      }

      // Client filter
      if (clientFilter && job.client_name !== clientFilter) {
        return false;
      }

      // Search query filter (search in title, JD ID, and client name)
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const titleMatch = job.title?.toLowerCase().includes(query);
        const idMatch = job.jd_unique_id?.toLowerCase().includes(query);
        const clientMatch = job.client_name?.toLowerCase().includes(query);
        
        if (!titleMatch && !idMatch && !clientMatch) {
          return false;
        }
      }

      return true;
    });
  }, [jobs, statusFilter, clientFilter, searchQuery]);

  const clearFilters = () => {
    setStatusFilter('all');
    setClientFilter('');
    setSearchQuery('');
  };

  const hasActiveFilters = statusFilter !== 'all' || clientFilter !== '' || searchQuery !== '';

  const handleInvoiceDateChange = async (jobId, date) => {
    try {
      // Fix timezone issue: Create date in local timezone to avoid day shift
      let formattedDate = null;
      if (date) {
        // Parse the date string (YYYY-MM-DD) and create a date in local timezone
        const dateParts = date.split('-');
        const year = parseInt(dateParts[0], 10);
        const month = parseInt(dateParts[1], 10) - 1; // Month is 0-indexed
        const day = parseInt(dateParts[2], 10);
        
        // Create date at local midnight to preserve the selected date
        const localDate = new Date(year, month, day, 12, 0, 0); // Use noon to avoid timezone edge cases
        formattedDate = localDate.toISOString();
      }
      
      const response = await api.patch(`/api/hr/jds/${jobId}/invoice-date`, {
        invoice_date: formattedDate
      });
      
      // Update the job in local state
      setJobs(prevJobs => 
        prevJobs.map(job => 
          job.id === jobId 
            ? { ...job, invoice_date: response.data.invoice_date }
            : job
        )
      );
    } catch (err) {
      console.error('Error updating invoice date:', err);
      alert('Failed to update invoice date. Please try again.');
    }
  };

  const handleRequirementFulfilledChange = async (jobId, fulfilled) => {
    try {
      const response = await api.patch(`/api/hr/jds/${jobId}/requirement-fulfilled`, {
        requirement_fulfilled: fulfilled
      });
      
      // Update the job in local state
      setJobs(prevJobs => 
        prevJobs.map(job => 
          job.id === jobId 
            ? { ...job, requirement_fulfilled: response.data.requirement_fulfilled }
            : job
        )
      );
    } catch (err) {
      console.error('Error updating requirement fulfilled status:', err);
      alert('Failed to update requirement fulfilled status. Please try again.');
    }
  };

  const handleDeleteJob = async (jobId, jobTitle) => {
    // Confirm deletion
    const confirmed = window.confirm(
      `Are you sure you want to delete the job "${jobTitle}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmed) {
      return;
    }
    
    try {
      await api.delete(`/api/hr/jds/${jobId}`);
      
      // Remove the job from local state
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
      
      // Show success message
      alert('Job deleted successfully');
    } catch (err) {
      console.error('Error deleting job:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to delete job. Please try again.';
      alert(errorMessage);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header 
          title="Jobs" 
          subtitle="Manage all job descriptions and positions"
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
          title="Jobs" 
          subtitle="Manage all job descriptions and positions"
        />
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={fetchJobs}
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
        title="Jobs" 
        subtitle="Manage all job descriptions and positions"
      />

      <div className="mt-6">
        {/* Action Bar */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            All Jobs {filteredJobs.length !== jobs.length && `(${filteredJobs.length} of ${jobs.length})`}
          </h3>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg font-medium flex items-center space-x-2 transition-colors ${
                showFilters || hasActiveFilters
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <FunnelIcon className="h-5 w-5" />
              <span>Filters</span>
              {hasActiveFilters && (
                <span className="ml-1 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {[statusFilter !== 'all', clientFilter, searchQuery].filter(Boolean).length}
                </span>
              )}
            </button>
            <button
              onClick={() => navigate('/hr/jd-manager')}
              className="btn-gradient-primary px-4 py-2 rounded-lg font-medium flex items-center space-x-2"
            >
              <PlusIcon className="h-5 w-5" />
              <span>Create JD</span>
            </button>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white rounded-xl shadow-sm p-6 mb-6 border border-gray-200"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search
                </label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by title, ID, or client..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              {/* Client Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Client
                </label>
                <select
                  value={clientFilter}
                  onChange={(e) => setClientFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Clients</option>
                  {uniqueClients.map((client) => (
                    <option key={client} value={client}>
                      {client}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={clearFilters}
                  className="text-sm text-gray-600 hover:text-gray-800 flex items-center space-x-1"
                >
                  <XMarkIcon className="h-4 w-4" />
                  <span>Clear Filters</span>
                </button>
              </div>
            )}
          </motion.div>
        )}

        {/* Jobs Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm overflow-hidden"
        >
          <div className="overflow-x-auto">
            {jobs.length > 0 ? (
              <>
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        JD ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Job Title
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Client Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Budget (₹)
                      </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Earning (₹)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invoice Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Requirement Fulfilled
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredJobs.length > 0 ? (
                      filteredJobs.map((job) => (
                    <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                      <td 
                        className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        onClick={() => navigate(`/hr/jd-manager`)}
                      >
                        <span className="text-xs font-mono text-gray-600">
                          {job.jd_unique_id || 'N/A'}
                        </span>
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/hr/jd-manager`)}
                      >
                        <div className="text-sm font-medium text-gray-900">{job.title}</div>
                      </td>
                      <td 
                        className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        onClick={() => navigate(`/hr/jd-manager`)}
                      >
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          job.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {job.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/hr/jd-manager`)}
                      >
                        <div className="text-sm text-gray-900">
                          {job.client_name || '-'}
                        </div>
                      </td>
                      <td 
                        className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        onClick={() => navigate(`/hr/jd-manager`)}
                      >
                        <div className="text-sm font-medium text-blue-600">
                          {job.budget_amount 
                            ? `₹${job.budget_amount.toLocaleString('en-IN')}` 
                            : '-'}
                        </div>
                      </td>
                      <td 
                        className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        onClick={() => navigate(`/hr/jd-manager`)}
                      >
                        <div className="text-sm font-medium text-green-600">
                          {job.your_earning 
                            ? `₹${job.your_earning.toLocaleString('en-IN')}` 
                            : '-'}
                        </div>
                      </td>
                      <td 
                        className="px-6 py-4 whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="relative">
                          <input
                            type="date"
                            value={job.invoice_date ? (() => {
                              // Fix timezone issue: Convert date to local date string
                              const date = new Date(job.invoice_date);
                              // Get local date components to avoid timezone shift
                              const year = date.getFullYear();
                              const month = String(date.getMonth() + 1).padStart(2, '0');
                              const day = String(date.getDate()).padStart(2, '0');
                              return `${year}-${month}-${day}`;
                            })() : ''}
                            onChange={(e) => handleInvoiceDateChange(job.id, e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                            placeholder="Select date"
                          />
                        </div>
                      </td>
                      <td 
                        className="px-6 py-4 whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <select
                          value={job.requirement_fulfilled ? 'fulfilled' : 'not_fulfilled'}
                          onChange={(e) => handleRequirementFulfilledChange(job.id, e.target.value === 'fulfilled')}
                          className={`px-3 py-2 text-sm font-medium rounded-lg border focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer ${
                            job.requirement_fulfilled
                              ? 'bg-green-100 text-green-800 border-green-300'
                              : 'bg-orange-100 text-orange-800 border-orange-300'
                          }`}
                        >
                          <option value="not_fulfilled">Not Fulfilled</option>
                          <option value="fulfilled">Fulfilled</option>
                        </select>
                      </td>
                      <td 
                        className="px-6 py-4 whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => handleDeleteJob(job.id, job.title)}
                          className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete Job"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </td>
                    </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="9" className="px-6 py-12 text-center">
                          <div className="flex flex-col items-center">
                            <BriefcaseIcon className="h-12 w-12 text-gray-400 mb-3" />
                            <p className="text-gray-500 font-medium">No jobs match your filters</p>
                            <button
                              onClick={clearFilters}
                              className="mt-2 text-blue-600 hover:text-blue-700 text-sm underline"
                            >
                              Clear filters
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </>
            ) : (
              <div className="p-12 text-center">
                <BriefcaseIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Job Descriptions</h3>
                <p className="text-gray-500 mb-6">Create your first job description to get started</p>
                <button
                  onClick={() => navigate('/hr/jd-manager')}
                  className="btn-gradient-primary px-6 py-3 rounded-lg font-medium"
                >
                  Create Job Description
                </button>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Jobs;

