import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  BuildingOfficeIcon, 
  UserIcon, 
  EnvelopeIcon,
  CalendarIcon,
  ArrowLeftIcon,
  TrashIcon,
  PencilIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import api from '../../utils/api';
import { useClients } from '../../store/clients';

const ClientDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { clients, removeClient } = useClients();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [sharedResumes, setSharedResumes] = useState([]);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [newStatus, setNewStatus] = useState('');

  useEffect(() => {
    // Find client from context or fetch if not available
    const foundClient = clients.find(c => c.id === id);
    if (foundClient) {
      setClient(foundClient);
      setLoading(false);
      fetchSharedResumes();
    } else {
      // If not in context, fetch from API
      fetchClient();
    }
  }, [id, clients]);

  useEffect(() => {
    if (client) {
      fetchSharedResumes();
    }
  }, [client]);

  const fetchClient = async () => {
    try {
      const response = await api.get(`/api/hr/clients/${id}`);
      setClient(response.data);
    } catch (error) {
      console.error('Error fetching client:', error);
      navigate('/hr/client-submit');
    } finally {
      setLoading(false);
    }
  };

  const fetchSharedResumes = async () => {
    try {
      setLoadingResumes(true);
      const response = await api.get(`/api/hr/clients/${id}/shared-resumes`);
      setSharedResumes(response.data.shared_resumes || []);
    } catch (error) {
      console.error('Error fetching shared resumes:', error);
      setSharedResumes([]);
    } finally {
      setLoadingResumes(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this client?')) {
      return;
    }

    setDeleting(true);
    try {
      await api.delete(`/api/hr/clients/${id}`);
      removeClient(id);
      navigate('/hr/client-submit');
    } catch (error) {
      console.error('Error deleting client:', error);
      alert('Failed to delete client');
    } finally {
      setDeleting(false);
    }
  };

  const handleViewResume = (resume) => {
    // Open resume in new tab
    if (resume.file_url) {
      window.open(resume.file_url, '_blank');
    } else {
      alert('Resume file not available');
    }
  };

  const handleUpdateStatus = (resume) => {
    setSelectedResume(resume);
    setNewStatus(resume.share_status);
    setShowStatusModal(true);
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

  const handleStatusUpdate = async () => {
    if (!selectedResume || !newStatus || newStatus === selectedResume.share_status) {
      setShowStatusModal(false);
      return;
    }

    try {
      // Update the share status
      await api.put(`/api/hr/resume/resume-shares/${selectedResume.share_id}`, {
        status: newStatus
      });

      // Refresh the shared resumes list
      await fetchSharedResumes();
      
      setShowStatusModal(false);
      alert(`Status updated to: ${newStatus}`);
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Failed to update status');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header title="Client Detail" subtitle="Loading client information..." />
        <div className="mt-6 flex justify-center">
          <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="p-6">
        <Header title="Client Not Found" subtitle="The requested client could not be found" />
        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/hr/client-submit')}
            className="btn-gradient-primary px-6 py-3 rounded-lg font-medium"
          >
            Back to Client Submit
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center mb-6">
        <button
          onClick={() => navigate('/hr/client-submit')}
          className="mr-4 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </button>
        <Header 
          title={client.name} 
          subtitle={`Client Details - ${client.company}`}
        />
      </div>

      <div className="max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm p-8"
        >
          {/* Client Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Basic Info */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Client Name
                </label>
                <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                  <UserIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-900">{client.name}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-900">{client.email}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company Name
                </label>
                <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                  <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-900">{client.company}</span>
                </div>
              </div>
            </div>

            {/* Additional Info */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Created Date
                </label>
                <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                  <CalendarIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-900">
                    {new Date(client.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Client ID
                </label>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="text-gray-900 font-mono text-sm">{client.id}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Shared Resumes Section */}
          <div className="mt-8 pt-8 border-t border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Shared Resumes</h3>
            
            {loadingResumes ? (
              <div className="flex justify-center py-8">
                <div className="spinner w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            ) : sharedResumes.length === 0 ? (
              <div className="text-center py-8">
                <DocumentTextIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">No resumes shared yet</h4>
                <p className="text-gray-500">Resumes shared with this client will appear here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {sharedResumes.map((resume, index) => (
                  <div key={resume.share_id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <UserIcon className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900">{resume.candidate_name}</h4>
                            <p className="text-sm text-gray-500">{resume.filename}</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                          <div>
                            <p className="text-xs font-medium text-gray-600 mb-1">Share Status</p>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              resume.share_status === 'shared' ? 'bg-blue-100 text-blue-800' :
                              resume.share_status === 'viewed' ? 'bg-green-100 text-green-800' :
                              resume.share_status === 'shortlisted' ? 'bg-yellow-100 text-yellow-800' :
                              resume.share_status === 'interview' ? 'bg-purple-100 text-purple-800' :
                              resume.share_status === 'offer' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {resume.share_status.charAt(0).toUpperCase() + resume.share_status.slice(1)}
                            </span>
                          </div>
                          
                          <div>
                            <p className="text-xs font-medium text-gray-600 mb-1">Resume Status</p>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              resume.resume_status === 'submission' ? 'bg-gray-100 text-gray-800' :
                              resume.resume_status === 'shortlisting' ? 'bg-yellow-100 text-yellow-800' :
                              resume.resume_status === 'interview' ? 'bg-purple-100 text-purple-800' :
                              resume.resume_status === 'offer_letter' ? 'bg-green-100 text-green-800' :
                              resume.resume_status === 'onboarding' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {getStatusLabel(resume.resume_status)}
                            </span>
                          </div>
                          
                          <div>
                            <p className="text-xs font-medium text-gray-600 mb-1">Shared Date</p>
                            <p className="text-sm text-gray-900">
                              {new Date(resume.shared_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        
                        {resume.skills && resume.skills.length > 0 && (
                          <div className="mt-3">
                            <p className="text-xs font-medium text-gray-600 mb-2">Skills</p>
                            <div className="flex flex-wrap gap-1">
                              {resume.skills.slice(0, 5).map((skill, skillIndex) => (
                                <span key={skillIndex} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                                  {skill}
                                </span>
                              ))}
                              {resume.skills.length > 5 && (
                                <span className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded">
                                  +{resume.skills.length - 5} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="ml-4 flex flex-col space-y-2">
                        <button 
                          onClick={() => handleViewResume(resume)}
                          className="px-3 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                        >
                          View Resume
                        </button>
                        <button 
                          onClick={() => handleUpdateStatus(resume)}
                          className="px-3 py-1 text-xs bg-gray-50 text-gray-700 rounded hover:bg-gray-100 transition-colors"
                        >
                          Update Status
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4 pt-8 border-t border-gray-200 mt-8">
            <button
              onClick={() => navigate('/hr/client-submit')}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Client Submit
            </button>
            
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {deleting ? (
                <>
                  <div className="spinner w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                  Deleting...
                </>
              ) : (
                <>
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete Client
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>

      {/* Status Update Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Update Status for {selectedResume?.candidate_name}
            </h3>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Current Status:</p>
              <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${
                selectedResume?.share_status === 'shared' ? 'bg-blue-100 text-blue-800' :
                selectedResume?.share_status === 'viewed' ? 'bg-green-100 text-green-800' :
                selectedResume?.share_status === 'shortlisted' ? 'bg-yellow-100 text-yellow-800' :
                selectedResume?.share_status === 'interview' ? 'bg-purple-100 text-purple-800' :
                selectedResume?.share_status === 'offer' ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {selectedResume?.share_status?.charAt(0).toUpperCase() + selectedResume?.share_status?.slice(1)}
              </span>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                New Status:
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="shared">Shared</option>
                <option value="viewed">Viewed</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="interview">Interview</option>
                <option value="offer">Offer</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => setShowStatusModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStatusUpdate}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Update Status
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientDetail;

