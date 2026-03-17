import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const ResumeSearch = ({ onSearch, onFilter }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'submission', label: 'Submission' },
    { value: 'shortlisting', label: 'Shortlisted' },
    { value: 'interview', label: 'Interview' },
    { value: 'select', label: 'Selected' },
    { value: 'reject', label: 'Rejected' },
    { value: 'offer_letter', label: 'Offer Letter' },
    { value: 'onboarding', label: 'Onboarding' },
  ];

  // Memoize search handler to prevent infinite re-renders
  const handleSearch = useCallback((query) => {
    if (onSearch) {
      onSearch(query);
    }
  }, [onSearch]);

  // Memoize filter handler to prevent infinite re-renders
  const handleFilter = useCallback((filters) => {
    if (onFilter) {
      onFilter(filters);
    }
  }, [onFilter]);

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      handleSearch(searchQuery);
    }, 300);

    return () => clearTimeout(delayedSearch);
  }, [searchQuery, handleSearch]);

  useEffect(() => {
    handleFilter({ status: statusFilter });
  }, [statusFilter, handleFilter]);

  const clearSearch = () => {
    setSearchQuery('');
    setStatusFilter('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-sm p-4 mb-6"
    >
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by candidate name, skills, or filename..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>

        {/* Filter Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
            showFilters || statusFilter
              ? 'border-blue-500 bg-blue-50 text-blue-700'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          <FunnelIcon className="h-5 w-5" />
          <span>Filters</span>
          {statusFilter && (
            <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
              1
            </span>
          )}
        </button>

        {/* Clear Button */}
        {(searchQuery || statusFilter) && (
          <button
            onClick={clearSearch}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 pt-4 border-t border-gray-200"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* ATS Score Range (Future Enhancement) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ATS Score Range
              </label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  placeholder="Max"
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Date Range (Future Enhancement) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Date
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>
          </div>

          {/* Quick Filter Tags */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quick Filters
            </label>
            <div className="flex flex-wrap gap-2">
              {['High ATS Score (>80)', 'Recent Uploads', 'Shared with Manager', 'Pending Review'].map((tag) => (
                <button
                  key={tag}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Search Summary */}
      {(searchQuery || statusFilter) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
            <span>Active filters:</span>
            {searchQuery && (
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                Search: "{searchQuery}"
              </span>
            )}
            {statusFilter && (
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
                Status: {statusOptions.find(s => s.value === statusFilter)?.label}
              </span>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default ResumeSearch;
