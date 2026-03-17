import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ExclamationTriangleIcon, 
  TrashIcon, 
  CheckCircleIcon,
  XMarkIcon,
  UserIcon,
  EnvelopeIcon,
  PhoneIcon
} from '@heroicons/react/24/outline';
import api from '../utils/api';

const DuplicateManager = ({ isOpen, onClose }) => {
  const [duplicateGroups, setDuplicateGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDuplicates, setSelectedDuplicates] = useState(new Set());
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchDuplicates();
    }
  }, [isOpen]);

  const fetchDuplicates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/hr/resumes/find-duplicates');
      setDuplicateGroups(response.data.duplicate_groups || []);
    } catch (error) {
      console.error('Error fetching duplicates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDuplicate = (duplicateId) => {
    const newSelected = new Set(selectedDuplicates);
    if (newSelected.has(duplicateId)) {
      newSelected.delete(duplicateId);
    } else {
      newSelected.add(duplicateId);
    }
    setSelectedDuplicates(newSelected);
  };

  const handleSelectAllInGroup = (group) => {
    const groupIds = group.duplicates.map(dup => dup.resume_id);
    const newSelected = new Set(selectedDuplicates);
    
    // If all are selected, deselect all
    const allSelected = groupIds.every(id => newSelected.has(id));
    if (allSelected) {
      groupIds.forEach(id => newSelected.delete(id));
    } else {
      groupIds.forEach(id => newSelected.add(id));
    }
    
    setSelectedDuplicates(newSelected);
  };

  const handleRemoveSelected = async () => {
    if (selectedDuplicates.size === 0) return;

    setRemoving(true);
    try {
      const duplicateIds = Array.from(selectedDuplicates);
      await api.delete('/api/hr/resumes/remove-duplicates', {
        data: { duplicate_ids: duplicateIds }
      });

      // Refresh the list
      await fetchDuplicates();
      setSelectedDuplicates(new Set());
      
      // Show success message
      alert(`Successfully removed ${duplicateIds.length} duplicate resumes`);
    } catch (error) {
      console.error('Error removing duplicates:', error);
      alert('Failed to remove duplicates. Please try again.');
    } finally {
      setRemoving(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  const getMatchReasonColor = (reason) => {
    switch (reason) {
      case 'name': return 'bg-blue-100 text-blue-800';
      case 'email': return 'bg-green-100 text-green-800';
      case 'phone': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="h-6 w-6 text-orange-500" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Manage Duplicate Resumes</h2>
              <p className="text-sm text-gray-600">
                Found {duplicateGroups.length} duplicate groups with {duplicateGroups.reduce((sum, group) => sum + group.count, 0)} total duplicates
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading duplicates...</span>
            </div>
          ) : duplicateGroups.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Duplicates Found</h3>
              <p className="text-gray-600">All resumes in your database are unique.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {duplicateGroups.map((group, groupIndex) => (
                <div key={group.group_id} className="border border-gray-200 rounded-lg p-4">
                  {/* Group Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <UserIcon className="h-5 w-5 text-gray-500" />
                      <div>
                        <h3 className="font-medium text-gray-900">{group.candidate_name}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          {group.candidate_email && (
                            <div className="flex items-center space-x-1">
                              <EnvelopeIcon className="h-4 w-4" />
                              <span>{group.candidate_email}</span>
                            </div>
                          )}
                          {group.candidate_phone && (
                            <div className="flex items-center space-x-1">
                              <PhoneIcon className="h-4 w-4" />
                              <span>{group.candidate_phone}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{group.count} duplicates</span>
                      <button
                        onClick={() => handleSelectAllInGroup(group)}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        {group.duplicates.every(dup => selectedDuplicates.has(dup.resume_id)) 
                          ? 'Deselect All' 
                          : 'Select All'
                        }
                      </button>
                    </div>
                  </div>

                  {/* Duplicates List */}
                  <div className="space-y-2">
                    {group.duplicates.map((duplicate, index) => (
                      <div
                        key={`${group.group_id}-${duplicate.resume_id}-${index}`}
                        className={`flex items-center justify-between p-3 rounded-lg border ${
                          selectedDuplicates.has(duplicate.resume_id)
                            ? 'border-blue-300 bg-blue-50'
                            : 'border-gray-200 bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={selectedDuplicates.has(duplicate.resume_id)}
                            onChange={() => handleSelectDuplicate(duplicate.resume_id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-900">
                                {duplicate.filename || `Resume ${index + 1}`}
                              </span>
                              <span className="text-sm text-gray-500">
                                Uploaded {formatDate(duplicate.uploaded_at)}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2 mt-1">
                              {duplicate.match_reasons.map((reason, reasonIndex) => (
                                <span
                                  key={`${duplicate.resume_id}-${reason}-${reasonIndex}`}
                                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getMatchReasonColor(reason)}`}
                                >
                                  {reason}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        <div className="text-sm text-gray-500">
                          Status: {duplicate.status}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {duplicateGroups.length > 0 && (
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-600">
              {selectedDuplicates.size} of {duplicateGroups.reduce((sum, group) => sum + group.count, 0)} duplicates selected
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                onClick={handleRemoveSelected}
                disabled={selectedDuplicates.size === 0 || removing}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {removing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Removing...</span>
                  </>
                ) : (
                  <>
                    <TrashIcon className="h-4 w-4" />
                    <span>Remove Selected ({selectedDuplicates.size})</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default DuplicateManager;
