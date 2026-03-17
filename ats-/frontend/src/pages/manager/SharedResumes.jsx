import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  DocumentCheckIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  EyeIcon,
  UserIcon,
  StarIcon,
} from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import EmptyState from '../../components/EmptyState';
import api, { getWebSocketUrl } from '../../utils/api';

const SharedResumes = () => {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedResume, setSelectedResume] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    fetchSharedResumes();
    
    // WebSocket connection for real-time updates
    const user_id = localStorage.getItem('user_id');
    const wsUrl = getWebSocketUrl(`/ws/resume-sync?user_id=${user_id}`);
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'resume_update') {
        fetchSharedResumes(); // Refresh on updates
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const fetchSharedResumes = async () => {
    try {
      const response = await api.get('/api/manager/resumes/shared');
      setResumes(response.data);
    } catch (error) {
      console.error('Error fetching shared resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateResumeStatus = async (resumeId, status) => {
    setActionLoading(resumeId);
    try {
      await api.patch(`/api/hr/resume/status?resume_id=${resumeId}`, { status });
      fetchSharedResumes(); // Refresh the list
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Failed to update status');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'submission': return 'bg-gray-100 text-gray-800';
      case 'shortlisting': return 'bg-blue-100 text-blue-800';
      case 'interview': return 'bg-purple-100 text-purple-800';
      case 'select': return 'bg-green-100 text-green-800';
      case 'reject': return 'bg-red-100 text-red-800';
      case 'offer_letter': return 'bg-yellow-100 text-yellow-800';
      case 'onboarding': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      submission: 'SUBMISSION',
      shortlisting: 'SHORTLISTED',
      interview: 'INTERVIEW',
      select: 'SELECTED',
      reject: 'REJECTED',
      offer_letter: 'OFFER LETTER',
      onboarding: 'ONBOARDING'
    };
    return labels[status] || status.replace('_', ' ').toUpperCase();
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header title="Shared Resumes" subtitle="Review resumes shared by HR team" />
        <div className="mt-6 flex justify-center">
          <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header 
        title="Shared Resumes" 
        subtitle="Review and take action on resumes shared by HR team"
      />

      <div className="mt-6">
        {resumes.length === 0 ? (
          <EmptyState
            icon={DocumentCheckIcon}
            title="No Shared Resumes"
            description="HR team hasn't shared any resumes with you yet"
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {resumes.map((resume, index) => (
              <motion.div
                key={resume.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-sm p-6 card-hover"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-modern rounded-full flex items-center justify-center">
                      <UserIcon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {resume.parsed_data?.name || 'Candidate'}
                      </h3>
                      <p className="text-sm text-gray-500">{resume.filename}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(resume.status)}`}>
                    {getStatusLabel(resume.status)}
                  </span>
                </div>

                {/* Resume Details */}
                <div className="space-y-3 mb-4">
                  {resume.parsed_data?.email && (
                    <p className="text-sm text-gray-600">{resume.parsed_data.email}</p>
                  )}
                  
                  {resume.parsed_data?.skills && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Skills:</p>
                      <div className="flex flex-wrap gap-1">
                        {resume.parsed_data.skills.slice(0, 3).map((skill, skillIndex) => (
                          <span
                            key={skillIndex}
                            className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
                          >
                            {skill}
                          </span>
                        ))}
                        {resume.parsed_data.skills.length > 3 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{resume.parsed_data.skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {resume.ats_score && (
                    <div className="flex items-center space-x-2">
                      <StarIcon className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm font-medium">ATS Score: {resume.ats_score}%</span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="space-y-2">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setSelectedResume(resume)}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                    >
                      <EyeIcon className="h-4 w-4 mr-1" />
                      View
                    </button>
                    <button
                      onClick={() => updateResumeStatus(resume.id, 'select')}
                      disabled={actionLoading === resume.id}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm disabled:opacity-50"
                    >
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                      {actionLoading === resume.id ? 'Processing...' : 'Approve'}
                    </button>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => updateResumeStatus(resume.id, 'reject')}
                      disabled={actionLoading === resume.id}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm disabled:opacity-50"
                    >
                      <XCircleIcon className="h-4 w-4 mr-1" />
                      Reject
                    </button>
                    <button
                      onClick={() => updateResumeStatus(resume.id, 'interview')}
                      disabled={actionLoading === resume.id}
                      className="flex-1 flex items-center justify-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm disabled:opacity-50"
                    >
                      Interview
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Resume Detail Modal */}
      {selectedResume && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedResume.parsed_data?.name || 'Candidate Profile'}
                  </h2>
                  <p className="text-gray-500">{selectedResume.filename}</p>
                </div>
                <button
                  onClick={() => setSelectedResume(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                {/* Status */}
                <div>
                  <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(selectedResume.status)}`}>
                    {selectedResume.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                {/* ATS Score */}
                {selectedResume.ats_score && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <StarIcon className="h-5 w-5 text-yellow-500" />
                      <span className="font-medium">ATS Score: {selectedResume.ats_score}%</span>
                    </div>
                  </div>
                )}

                {/* Parsed Data */}
                {selectedResume.parsed_data && (
                  <div className="space-y-4">
                    {selectedResume.parsed_data.email && (
                      <div>
                        <span className="font-medium text-gray-700">Email:</span>
                        <span className="ml-2">{selectedResume.parsed_data.email}</span>
                      </div>
                    )}

                    {selectedResume.parsed_data.skills && selectedResume.parsed_data.skills.length > 0 && (
                      <div>
                        <span className="font-medium text-gray-700">Skills:</span>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {selectedResume.parsed_data.skills.map((skill, index) => (
                            <span
                              key={index}
                              className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedResume.parsed_data.summary && (
                      <div>
                        <span className="font-medium text-gray-700">Summary:</span>
                        <p className="mt-1 text-gray-600 leading-relaxed">
                          {selectedResume.parsed_data.summary}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex space-x-3 pt-4 border-t border-gray-200">
                  <button
                    onClick={async () => {
                      try {
                        // First, get the resume details to get the filename
                        const resumeResponse = await api.get(`/api/hr/resumes/${selectedResume.id}`);
                        const resume = resumeResponse.data;
                        
                        // Download the file using the correct endpoint
                        const response = await api.get(`/api/hr/resume/download/${selectedResume.id}`, { 
                          responseType: 'blob' 
                        });
                        
                        // Create blob URL and trigger download
                        const url = window.URL.createObjectURL(new Blob([response.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', resume.filename || `resume_${selectedResume.id}.pdf`);
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                      } catch (error) {
                        console.error('Error downloading resume:', error);
                        const errorMessage = error.response?.data?.detail || 'Failed to download resume.';
                        alert(errorMessage);
                      }
                    }}
                    className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    Download Resume
                  </button>
                  <button
                    onClick={() => {
                      updateResumeStatus(selectedResume.id, 'interview');
                      setSelectedResume(null);
                    }}
                    className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Send Interview
                  </button>
                  <button
                    onClick={() => {
                      // Generate offer action
                      alert('Offer generation feature coming soon!');
                    }}
                    className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors"
                  >
                    Generate Offer
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default SharedResumes;
