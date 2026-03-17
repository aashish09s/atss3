import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ExclamationTriangleIcon, 
  XMarkIcon, 
  UserIcon, 
  EnvelopeIcon, 
  PhoneIcon,
  DocumentTextIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import api from '../utils/api';

const DuplicateDetectionModal = ({ 
  isOpen, 
  onClose, 
  duplicates, 
  candidateInfo, 
  onRemoveDuplicates,
  isBulkUpload = false 
}) => {
  const [selectedDuplicates, setSelectedDuplicates] = useState([]);
  const [removing, setRemoving] = useState(false);

  if (!isOpen) return null;

  const handleSelectDuplicate = (duplicateId) => {
    setSelectedDuplicates(prev => 
      prev.includes(duplicateId) 
        ? prev.filter(id => id !== duplicateId)
        : [...prev, duplicateId]
    );
  };

  const handleSelectAll = () => {
    if (selectedDuplicates.length === duplicates.length) {
      setSelectedDuplicates([]);
    } else {
      setSelectedDuplicates(duplicates.map(dup => dup.resume_id));
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      submission: 'Submission',
      shortlisting: 'Shortlisted',
      interview: 'Interview',
      select: 'Selected',
      reject: 'Rejected',
      offer_letter: 'Offer Letter',
      onboarding: 'Onboarding'
    };
    return labels[status] || status.charAt(0).toUpperCase() + status.slice(1);
  };

  const handleRemoveSelected = async () => {
    if (selectedDuplicates.length === 0) return;

    setRemoving(true);
    try {
      await api.delete('/api/hr/resumes/remove-duplicates', {
        data: { duplicate_ids: selectedDuplicates }
      });
      
      onRemoveDuplicates(selectedDuplicates);
      setSelectedDuplicates([]);
      
      // If all duplicates are removed, close modal
      if (selectedDuplicates.length === duplicates.length) {
        onClose();
      }
    } catch (error) {
      console.error('Error removing duplicates:', error);
      alert('Failed to remove duplicates');
    } finally {
      setRemoving(false);
    }
  };

  const getMatchReasonColor = (reason) => {
    switch (reason) {
      case 'name': return 'bg-blue-100 text-blue-800';
      case 'email': return 'bg-green-100 text-green-800';
      case 'phone': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
              <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {isBulkUpload ? 'Duplicate Resumes Detected' : 'Duplicate Resume Detected'}
              </h3>
              <p className="text-sm text-gray-500">
                {isBulkUpload 
                  ? `Found ${duplicates.length} duplicate resumes in your upload`
                  : 'This resume appears to be a duplicate of existing resumes'
                }
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {/* Candidate Info */}
          {candidateInfo && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">New Resume Information:</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-2">
                  <UserIcon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">{candidateInfo.name || 'Unknown'}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <EnvelopeIcon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">{candidateInfo.email || 'Not provided'}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <PhoneIcon className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">{candidateInfo.phone || 'Not provided'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Duplicates List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">Existing Duplicate Resumes:</h4>
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                {selectedDuplicates.length === duplicates.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            {duplicates.map((duplicate, index) => (
              <div
                key={duplicate.resume_id}
                className={`border rounded-lg p-4 transition-colors ${
                  selectedDuplicates.includes(duplicate.resume_id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start space-x-4">
                  <input
                    type="checkbox"
                    checked={selectedDuplicates.includes(duplicate.resume_id)}
                    onChange={() => handleSelectDuplicate(duplicate.resume_id)}
                    className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <DocumentTextIcon className="w-5 h-5 text-gray-400" />
                      <h5 className="font-medium text-gray-900">{duplicate.candidate_name}</h5>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        duplicate.status === 'submission' ? 'bg-gray-100 text-gray-800' :
                        duplicate.status === 'shortlisting' ? 'bg-yellow-100 text-yellow-800' :
                        duplicate.status === 'interview' ? 'bg-purple-100 text-purple-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {getStatusLabel(duplicate.status)}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                      <div className="flex items-center space-x-2">
                        <EnvelopeIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">{duplicate.candidate_email || 'Not provided'}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <PhoneIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">{duplicate.candidate_phone || 'Not provided'}</span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Uploaded: {new Date(duplicate.uploaded_at).toLocaleDateString()}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">Match reasons:</span>
                      {duplicate.match_reasons.map((reason, idx) => (
                        <span
                          key={idx}
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getMatchReasonColor(reason)}`}
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-600">
            {selectedDuplicates.length > 0 && (
              <span>{selectedDuplicates.length} duplicate(s) selected for removal</span>
            )}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {isBulkUpload ? 'Keep All' : 'Cancel Upload'}
            </button>
            {selectedDuplicates.length > 0 && (
              <button
                onClick={handleRemoveSelected}
                disabled={removing}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {removing ? (
                  <>
                    <div className="spinner w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                    <span>Removing...</span>
                  </>
                ) : (
                  <>
                    <TrashIcon className="w-4 h-4" />
                    <span>Remove Selected ({selectedDuplicates.length})</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default DuplicateDetectionModal;
