import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UserIcon, 
  EyeIcon, 
  DocumentArrowDownIcon,
  ShareIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ClockIcon,
  EnvelopeIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import ResumeSearch from '../../components/ResumeSearch';
import ResumeDetailView from '../../components/ResumeDetailView';
import InterviewEmailForm from '../../components/InterviewEmailForm';
import LoadingSpinner, { CardSkeleton } from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import DuplicateDetectionModal from '../../components/DuplicateDetectionModal';
import DuplicateManager from '../../components/DuplicateManager';
import { showNotification } from '../../components/NotificationSystem';
import api from '../../utils/api';
import ShareResumeModal from '../../components/ShareResumeModal';

const ResumeList = () => {
  const [resumes, setResumes] = useState([]);
  const [filteredResumes, setFilteredResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedResume, setSelectedResume] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({});
  const [actionLoading, setActionLoading] = useState({});
  const [showInterviewEmailForm, setShowInterviewEmailForm] = useState(false);
  const [selectedResumeForEmail, setSelectedResumeForEmail] = useState(null);
  const [selectedResumeForShare, setSelectedResumeForShare] = useState(null);
  const [resendableResumes, setResendableResumes] = useState({});
  const [selectedResumes, setSelectedResumes] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateData, setDuplicateData] = useState(null);
  const [showDuplicateManager, setShowDuplicateManager] = useState(false);

  useEffect(() => {
    fetchResumes();
  }, []);

  useEffect(() => {
    filterResumes();
  }, [resumes, searchQuery, filters]);

  const fetchResumes = async () => {
    try {
      const response = await api.get('/api/hr/resumes/', {
        params: {
          limit: 100,
          offset: 0
        }
      });
      setResumes(response.data);
    } catch (error) {
      console.error('Error fetching resumes:', error);
      showNotification('Error', 'Failed to load resumes', 'error');
    } finally {
      setLoading(false);
    }
  };

  const filterResumes = () => {
    let filtered = [...resumes];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(resume => 
        resume.parsed_data?.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        resume.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        resume.parsed_data?.skills?.some(skill => 
          skill.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }

    // Apply status filter
    if (filters.status) {
      filtered = filtered.filter(resume => resume.status === filters.status);
    }

    setFilteredResumes(filtered);
  };

  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
  }, []);

  const handleFilter = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  const handleAction = async (action, resumeId) => {
    setActionLoading(prev => ({ ...prev, [resumeId]: action }));

    try {
      switch (action) {
        case 'download':
          await handleDownload(resumeId);
          break;
        case 'share':
          handleShare(resumeId);
          break;
        case 'delete':
          await handleDelete(resumeId);
          break;
        case 'email':
          await handleSendInterviewEmail(resumeId);
          break;
        default:
          break;
      }
    } catch (error) {
      console.error(`Error ${action}:`, error);
      const detailMessage = error?.response?.data?.detail || error?.message;
      showNotification('Error', detailMessage || `Failed to ${action} resume`, 'error');
    } finally {
      setActionLoading(prev => ({ ...prev, [resumeId]: null }));
    }
  };

  const handleDownload = async (resumeId) => {
    const resume = resumes.find(r => r.id === resumeId);

    const response = await api.get(`/api/hr/resume/download/${resumeId}`, {
      responseType: 'arraybuffer'
    });

    // Determine filename from Content-Disposition header or fallback to stored filename
    const disposition = response.headers['content-disposition'];
    let filename = resume?.filename || `resume-${resumeId}`;

    if (disposition) {
      // Try to extract UTF-8 encoded filename first
      const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      const regularMatch = disposition.match(/filename="?([^";]+)"?/i);

      if (utf8Match && utf8Match[1]) {
        try {
          filename = decodeURIComponent(utf8Match[1]);
        } catch (error) {
          console.warn('Failed to decode UTF-8 filename, falling back to default', error);
        }
      } else if (regularMatch && regularMatch[1]) {
        filename = regularMatch[1];
      }
    }

    // Ensure filename has an extension
    if (!/\.[A-Za-z0-9]+$/.test(filename) && resume?.filename) {
      filename = resume.filename;
    }

    const blob = new Blob([response.data], {
      type: response.headers['content-type'] || 'application/octet-stream'
    });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    showNotification('Success', 'Resume downloaded successfully', 'success');
  };

  const handleShare = (resumeId) => {
    const resume = resumes.find(r => r.id === resumeId);
    if (!resume) {
      showNotification('Error', 'Resume not found', 'error');
      return;
    }
    setSelectedResumeForShare(resume);
  };

  const handleDelete = async (resumeId) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) {
      return;
    }

    await api.delete(`/api/hr/resumes/${resumeId}`);
    
    setResumes(prev => prev.filter(resume => resume.id !== resumeId));
    showNotification('Success', 'Resume deleted successfully', 'success');
  };

  const handleSendInterviewEmail = async (resumeId) => {
    const resume = resumes.find(r => r.id === resumeId);
    if (!resume?.parsed_data?.email) {
      showNotification('Error', 'No email address found for this candidate', 'error');
      return;
    }

    setSelectedResumeForEmail(resume);
    setShowInterviewEmailForm(true);
  };

  const handleInterviewEmailSent = () => {
    setShowInterviewEmailForm(false);
    setSelectedResumeForEmail(null);
    // Optionally refresh the resume list or update status
  };

  const handleDuplicateDetection = (duplicateInfo) => {
    setDuplicateData(duplicateInfo);
    setShowDuplicateModal(true);
  };

  const handleRemoveDuplicates = (removedIds) => {
    // Remove the duplicates from the current resume list
    setResumes(prevResumes => 
      prevResumes.filter(resume => !removedIds.includes(resume.id))
    );
    setFilteredResumes(prevFiltered => 
      prevFiltered.filter(resume => !removedIds.includes(resume.id))
    );
    
    showNotification('Success', `${removedIds.length} duplicate resume(s) removed successfully`, 'success');
  };

  const handleCloseDuplicateModal = () => {
    setShowDuplicateModal(false);
    setDuplicateData(null);
  };

  const handleSelectResume = (resumeId) => {
    setSelectedResumes(prev => {
      if (prev.includes(resumeId)) {
        return prev.filter(id => id !== resumeId);
      } else {
        return [...prev, resumeId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedResumes([]);
    } else {
      setSelectedResumes(filteredResumes.map(resume => resume.id));
    }
    setSelectAll(!selectAll);
  };

  const handleBulkShareWithClient = () => {
    if (selectedResumes.length === 0) {
      showNotification('Error', 'Please select at least one resume', 'error');
      return;
    }
    // This will be handled by the share panel
    setSelectedResume({ id: 'bulk', selectedIds: selectedResumes });
  };


  const getStatusColor = (status) => {
    const colors = {
      submission: 'bg-gray-100 text-gray-800',
      shortlisting: 'bg-yellow-100 text-yellow-800',
      interview: 'bg-blue-100 text-blue-800',
      select: 'bg-green-100 text-green-800',
      reject: 'bg-red-100 text-red-800',
      offer_letter: 'bg-purple-100 text-purple-800',
      onboarding: 'bg-indigo-100 text-indigo-800'
    };
    return colors[status] || colors.submission;
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
    return labels[status] || status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'select':
        return <CheckCircleIcon className="w-4 h-4" />;
      case 'interview':
        return <ClockIcon className="w-4 h-4" />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header title="Resume Management" subtitle="Manage and review candidate resumes" />
        <div className="mt-6">
          <CardSkeleton count={6} />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header title="Resume Management" subtitle="Manage and review candidate resumes" />

      {/* Search and Filters */}
      <ResumeSearch onSearch={handleSearch} onFilter={handleFilter} />

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Resumes</p>
              <p className="text-2xl font-bold text-gray-900">{resumes.length}</p>
            </div>
            <UserIcon className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Shortlisted</p>
              <p className="text-2xl font-bold text-yellow-600">
                {resumes.filter(r => r.status === 'shortlisting').length}
              </p>
            </div>
            <FunnelIcon className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Interviews</p>
              <p className="text-2xl font-bold text-blue-600">
                {resumes.filter(r => r.status === 'interview').length}
              </p>
            </div>
            <ClockIcon className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Selected</p>
              <p className="text-2xl font-bold text-green-600">
                {resumes.filter(r => r.status === 'select').length}
              </p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowDuplicateManager(true)}
            className="inline-flex items-center px-4 py-2 border border-orange-300 rounded-md shadow-sm text-sm font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
          >
            <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
            Manage Duplicates
          </button>
        </div>
        <div className="text-sm text-gray-600">
          {resumes.length} total resumes
        </div>
      </div>

      {/* Resume Grid */}
      {filteredResumes.length === 0 ? (
        <EmptyState 
          icon={UserIcon}
          title="No resumes found"
          description="Try adjusting your search criteria or upload new resumes"
        />
      ) : (
        <div>
          {/* Bulk Actions Bar */}
          {selectedResumes.length > 0 && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-blue-900">
                    {selectedResumes.length} resume{selectedResumes.length > 1 ? 's' : ''} selected
                  </span>
                  <button
                    onClick={handleBulkShareWithClient}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
                  >
                    Share with Client (Email)
                  </button>
                </div>
                <button
                  onClick={() => setSelectedResumes([])}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {filteredResumes.map((resume, index) => (
                <motion.div
                  key={resume.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className={`bg-white rounded-xl shadow-sm border overflow-hidden hover:shadow-md transition-shadow group ${
                    selectedResumes.includes(resume.id) ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'
                  }`}
                >
                  {/* Card Header */}
                  <div className="p-4 border-b border-gray-100">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        {/* Selection Checkbox */}
                        <input
                          type="checkbox"
                          checked={selectedResumes.includes(resume.id)}
                          onChange={() => handleSelectResume(resume.id)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <UserIcon className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium text-gray-900 truncate">
                          {resume.parsed_data?.name && resume.parsed_data.name !== 'Unknown' 
                            ? resume.parsed_data.name 
                            : (resume.parsed_data?.candidate_name || 'Unknown Candidate')}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">{resume.filename}</p>
                      </div>
                    </div>
                    
                    {resume.shared_with_manager && (
                      <div className="ml-2 flex-shrink-0">
                        <ShareIcon className="w-4 h-4 text-green-500" />
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-4">
                  {/* Status */}
                  <div className="flex items-center justify-between mb-3">
                    <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(resume.status)}`}>
                      {getStatusIcon(resume.status)}
                      <span>{getStatusLabel(resume.status)}</span>
                    </span>
                    
                    {resume.ats_score && (
                      <div className="flex items-center space-x-1 text-sm text-gray-600">
                        <ChartBarIcon className="w-4 h-4" />
                        <span>{resume.ats_score}%</span>
                      </div>
                    )}
                  </div>

                  {/* Skills Preview */}
                  {resume.parsed_data?.skills?.length > 0 && (
                    <div className="mb-3">
                      <div className="flex flex-wrap gap-1">
                        {resume.parsed_data.skills.slice(0, 3).map((skill, skillIndex) => (
                          <span
                            key={skillIndex}
                            className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                          >
                            {skill}
                          </span>
                        ))}
                        {resume.parsed_data.skills.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">
                            +{resume.parsed_data.skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Experience Preview */}
                  {resume.parsed_data?.experience?.length > 0 && (
                    <div className="mb-3">
                      <h4 className="text-xs font-medium text-gray-700 mb-1">Experience</h4>
                      <div className="space-y-1">
                        {resume.parsed_data.experience.slice(0, 2).map((exp, expIndex) => (
                          <div key={expIndex} className="text-xs text-gray-600">
                            {typeof exp === 'string' ? (
                              <p className="truncate">{exp}</p>
                            ) : (
                              <p className="truncate">
                                {exp.title || exp.position || 'Position'} 
                                {exp.company && ` at ${exp.company}`}
                              </p>
                            )}
                          </div>
                        ))}
                        {resume.parsed_data.experience.length > 2 && (
                          <p className="text-xs text-gray-500">
                            +{resume.parsed_data.experience.length - 2} more
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Summary Preview */}
                  {resume.parsed_data?.summary && (
                    <div className="mb-3">
                      <h4 className="text-xs font-medium text-gray-700 mb-2">Summary</h4>
                      <div className="bg-gray-50 rounded-lg p-3 border-l-4 border-blue-200">
                        <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">
                          {resume.parsed_data.summary.length > 120 
                            ? `${resume.parsed_data.summary.substring(0, 120)}...` 
                            : resume.parsed_data.summary
                          }
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Upload Date */}
                  <p className="text-xs text-gray-500 mb-4">
                    Uploaded {new Date(resume.created_at).toLocaleDateString()}
                  </p>

                  {/* Action Buttons */}
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setSelectedResume(resume)}
                      className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition-colors"
                    >
                      <EyeIcon className="w-4 h-4" />
                      <span>View</span>
                    </button>
                    
                    <button
                      onClick={() => handleAction('download', resume.id)}
                      disabled={actionLoading[resume.id] === 'download'}
                      className="p-2 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {actionLoading[resume.id] === 'download' ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <DocumentArrowDownIcon className="w-4 h-4" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => handleAction('share', resume.id)}
                      className="p-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-lg transition-colors"
                    >
                      <ShareIcon className="w-4 h-4" />
                    </button>
                    
                    {resume.parsed_data?.email && (
                      <button
                        onClick={() => handleAction('email', resume.id)}
                        disabled={actionLoading[resume.id] === 'email'}
                        className="p-2 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg transition-colors disabled:opacity-50"
                        title="Send Interview Email"
                      >
                        {actionLoading[resume.id] === 'email' ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <EnvelopeIcon className="w-4 h-4" />
                        )}
                      </button>
                    )}
                    
                    <button
                      onClick={() => handleAction('delete', resume.id)}
                      disabled={actionLoading[resume.id] === 'delete'}
                      className="p-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {actionLoading[resume.id] === 'delete' ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <TrashIcon className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        </div>
      )}

      {/* Resume Detail Modal */}
      {selectedResume && (
        <ResumeDetailView
          resume={selectedResume}
          onClose={() => setSelectedResume(null)}
          onUpdate={(updatedResume) => {
            setResumes(prev => prev.map(resume => 
              resume.id === updatedResume.id ? updatedResume : resume
            ));
            setSelectedResume(updatedResume);
          }}
        />
      )}

      {/* Interview Email Form Modal */}
      {showInterviewEmailForm && selectedResumeForEmail && (
        <InterviewEmailForm
          isOpen={showInterviewEmailForm}
          onClose={() => {
            setShowInterviewEmailForm(false);
            setSelectedResumeForEmail(null);
          }}
          resume={selectedResumeForEmail}
          showNotification={showNotification}
        />
      )}

      {selectedResumeForShare && (
        <ShareResumeModal
          resume={selectedResumeForShare}
          onClose={() => setSelectedResumeForShare(null)}
          onShared={(updatedFields) => {
            const { managerShared, clientShared } = updatedFields;
            setResumes(prev => prev.map(resume => 
              resume.id === selectedResumeForShare.id ? {
                ...resume,
                shared_with_manager: managerShared ?? resume.shared_with_manager,
                client_shared_status: clientShared ?? resume.client_shared_status,
              } : resume
            ));
            setSelectedResumeForShare(null);
          }}
          showNotification={showNotification}
        />
      )}

      {/* Duplicate Detection Modal */}
      {showDuplicateModal && duplicateData && (
        <DuplicateDetectionModal
          isOpen={showDuplicateModal}
          onClose={handleCloseDuplicateModal}
          duplicates={duplicateData.duplicates}
          candidateInfo={duplicateData.candidateInfo}
          onRemoveDuplicates={handleRemoveDuplicates}
          isBulkUpload={duplicateData.isBulkUpload || false}
        />
      )}

      {/* Duplicate Manager Modal */}
      {showDuplicateManager && (
        <DuplicateManager
          isOpen={showDuplicateManager}
          onClose={() => {
            setShowDuplicateManager(false);
            fetchResumes(); // Refresh the resume list after managing duplicates
          }}
        />
      )}
    </div>
  );
};

export default ResumeList;
