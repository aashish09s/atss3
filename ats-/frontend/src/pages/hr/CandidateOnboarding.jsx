import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  EnvelopeIcon, 
  UserIcon, 
  CalendarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  XMarkIcon,
  DocumentIcon,
  PhotoIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import api from '../../utils/api';
import { formatLocalDate, formatLocalDateTime } from '../../utils/dateUtils';

const CandidateOnboarding = () => {
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [emailForm, setEmailForm] = useState({
    candidate_email: '',
    candidate_name: '',
    position: '',
    company_name: ''
  });
  const [onboardingRequests, setOnboardingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [requestToDelete, setRequestToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchOnboardingRequests();
  }, []);

  const fetchOnboardingRequests = async () => {
    try {
      const response = await api.get('/api/hr/candidate-onboarding');
      setOnboardingRequests(response.data);
    } catch (error) {
      console.error('Error fetching onboarding requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendOnboarding = async (e) => {
    e.preventDefault();
    setSending(true);
    
    try {
      await api.post('/api/hr/candidate-onboarding/send', emailForm);
      setShowEmailForm(false);
      setEmailForm({
        candidate_email: '',
        candidate_name: '',
        position: '',
        company_name: ''
      });
      fetchOnboardingRequests();
      alert('Onboarding email sent successfully!');
    } catch (error) {
      console.error('Error sending onboarding email:', error);
      alert('Failed to send onboarding email');
    } finally {
      setSending(false);
    }
  };

  const handleViewDetails = async (requestId) => {
    setDetailsLoading(true);
    try {
      const response = await api.get(`/api/hr/candidate-onboarding/${requestId}/details`);
      setSelectedRequest(response.data);
      setShowDetailsModal(true);
    } catch (error) {
      console.error('Error fetching request details:', error);
      alert('Failed to fetch request details');
    } finally {
      setDetailsLoading(false);
    }
  };

  const documentConfig = [
    { key: 'resume', label: 'Resume', icon: DocumentIcon },
    { key: 'degree', label: 'Degree Certificate', icon: DocumentIcon },
    { key: 'photo', label: 'Photo', icon: PhotoIcon },
    { key: 'bank_details', label: 'Bank Details', icon: DocumentIcon },
    { key: 'aadhar_card', label: 'Aadhar Card', icon: DocumentIcon },
    { key: 'pan_card', label: 'PAN Card', icon: DocumentIcon },
    { key: 'id_proof', label: 'ID Proof', icon: DocumentIcon }
  ];

  const getDocumentDownloadUrl = (requestId, docKey) => `/api/hr/candidate-onboarding/${requestId}/documents/${docKey}`;
  const getArchiveDownloadUrl = (requestId) => `/api/hr/candidate-onboarding/${requestId}/documents/archive`;

  const handleResend = async (requestId) => {
    try {
      await api.post(`/api/hr/candidate-onboarding/${requestId}/resend`);
      alert('Onboarding email resent successfully!');
      fetchOnboardingRequests(); // Refresh the list
    } catch (error) {
      console.error('Error resending onboarding email:', error);
      alert('Failed to resend onboarding email');
    }
  };

  const handleDelete = async (requestId) => {
    try {
      setDeleting(true);
      await api.delete(`/api/hr/candidate-onboarding/${requestId}`);
      alert('Onboarding request deleted successfully!');
      fetchOnboardingRequests(); // Refresh the list
      setShowDeleteModal(false);
      setRequestToDelete(null);
    } catch (error) {
      console.error('Error deleting onboarding request:', error);
      alert('Failed to delete onboarding request');
    } finally {
      setDeleting(false);
    }
  };

  const confirmDelete = (request) => {
    setRequestToDelete(request);
    setShowDeleteModal(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'expired':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-4 w-4" />;
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4" />;
      case 'expired':
        return <XCircleIcon className="h-4 w-4" />;
      default:
        return <ClockIcon className="h-4 w-4" />;
    }
  };

  const formatDate = (dateString) => {
    return formatLocalDateTime(dateString, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Candidate Onboarding</h1>
          <p className="mt-2 text-gray-600">
            Send onboarding invitations to candidates and track their progress
          </p>
        </div>

        {/* Send Onboarding Button */}
        <div className="mb-8">
          <button
            onClick={() => setShowEmailForm(true)}
            className="btn-gradient-primary px-6 py-3 rounded-lg font-medium flex items-center space-x-2"
          >
            <EnvelopeIcon className="h-5 w-5" />
            <span>Send Onboarding Invitation</span>
          </button>
        </div>

        {/* Onboarding Requests Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Onboarding Requests</h2>
          </div>
          
          {loading ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading...</p>
            </div>
          ) : onboardingRequests.length === 0 ? (
            <div className="p-6 text-center">
              <UserIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No onboarding requests yet</h3>
              <p className="text-gray-500">Send your first onboarding invitation to get started.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Candidate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Position
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sent Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expires
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {onboardingRequests.map((request) => (
                    <tr key={request.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {request.candidate_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {request.candidate_email}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {request.position}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {getStatusIcon(request.status)}
                          <span className="ml-1 capitalize">{request.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(request.sent_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(request.expires_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {request.status === 'completed' && (
                          <button
                            onClick={() => handleViewDetails(request.id)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Details
                          </button>
                        )}
                        {request.status === 'pending' && (
                          <button
                            onClick={() => handleResend(request.id)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Resend
                          </button>
                        )}
                        {request.status === 'expired' && (
                          <button
                            onClick={() => confirmDelete(request)}
                            className="text-red-600 hover:text-red-900 flex items-center space-x-1"
                          >
                            <TrashIcon className="h-4 w-4" />
                            <span>Delete</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Timezone Info */}
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
            <div className="text-center space-y-1">
              <p className="text-xs text-gray-500">
                All times are displayed in your local timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}
              </p>
              <p className="text-xs text-blue-600">
                Times are automatically converted from UTC to your local timezone
              </p>
            </div>
          </div>
        </div>

        {/* Timezone Debug Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4"
        >
          <h4 className="font-medium text-blue-900 mb-3">Timezone Debug Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <strong>Your Timezone:</strong> {Intl.DateTimeFormat().resolvedOptions().timeZone}
            </div>
            <div>
              <strong>Current Local Time:</strong> {new Date().toLocaleString()}
            </div>
            <div>
              <strong>Current UTC Time:</strong> {new Date().toUTCString()}
            </div>
            <div>
              <strong>Timezone Offset:</strong> {-(new Date().getTimezoneOffset() / 60)} hours from UTC
            </div>
          </div>
          <p className="text-xs text-blue-600 mt-3">
            If you still see time differences, this is likely due to the backend storing times in UTC. 
            The frontend automatically converts these to your local timezone for display.
          </p>
        </motion.div>

        {/* Send Onboarding Email Modal */}
        {showEmailForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white rounded-lg max-w-md w-full"
            >
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Send Onboarding Invitation</h3>
                
                <form onSubmit={handleSendOnboarding} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Candidate Email *
                    </label>
                    <input
                      type="email"
                      value={emailForm.candidate_email}
                      onChange={(e) => setEmailForm({ ...emailForm, candidate_email: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="candidate@example.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Candidate Name *
                    </label>
                    <input
                      type="text"
                      value={emailForm.candidate_name}
                      onChange={(e) => setEmailForm({ ...emailForm, candidate_name: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Position *
                    </label>
                    <input
                      type="text"
                      value={emailForm.position}
                      onChange={(e) => setEmailForm({ ...emailForm, position: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Software Engineer"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Company Name *
                    </label>
                    <input
                      type="text"
                      value={emailForm.company_name}
                      onChange={(e) => setEmailForm({ ...emailForm, company_name: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Your Company"
                    />
                  </div>

                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowEmailForm(false)}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={sending}
                      className="btn-gradient-primary px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                    >
                      {sending ? 'Sending...' : 'Send Invitation'}
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {showDetailsModal && selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold">Onboarding Details</h3>
                <button
                  onClick={() => {
                    setShowDetailsModal(false);
                    setSelectedRequest(null);
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {detailsLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Candidate Information */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-lg mb-3 text-gray-800">Candidate Information</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Full Name</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.full_name || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Email</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.email || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Phone</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.phone || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Date of Birth</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.dob || 'N/A'}</p>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-600">Address</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.address || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">City</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.city || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">State</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.state || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Pincode</label>
                        <p className="text-gray-900">{selectedRequest.personal_details?.pincode || 'N/A'}</p>
                      </div>
                    </div>
                  </div>

                  {/* Documents */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-lg mb-3 text-gray-800">Documents</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {documentConfig.map(({ key, label, icon: Icon }) => {
                        if (!selectedRequest.documents?.[key]) return null;
                        return (
                          <div key={key}>
                            <label className="block text-sm font-medium text-gray-600 mb-2">{label}</label>
                            <a
                              href={getDocumentDownloadUrl(selectedRequest.id, key)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                            >
                              <Icon className="h-4 w-4 mr-2" />
                              Download
                            </a>
                          </div>
                        );
                      })}
                    </div>

                    <div className="mt-4">
                      <a
                        href={getArchiveDownloadUrl(selectedRequest.id)}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <DocumentIcon className="h-4 w-4 mr-2" />
                        Download All Documents (ZIP)
                      </a>
                    </div>
                  </div>

                  {/* Submission Info */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-lg mb-3 text-gray-800">Submission Details</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Submitted At</label>
                        <p className="text-gray-900">{formatDate(selectedRequest.submitted_at)}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600">Status</label>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedRequest.status)}`}>
                          {getStatusIcon(selectedRequest.status)}
                          {selectedRequest.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && requestToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-lg max-w-md w-full"
          >
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <TrashIcon className="h-6 w-6 text-red-600" />
                </div>
              </div>
              
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Delete Onboarding Request
                </h3>
                <p className="text-sm text-gray-600">
                  Are you sure you want to delete the onboarding request for{' '}
                  <span className="font-medium">{requestToDelete.candidate_name}</span>?
                  This action cannot be undone.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setRequestToDelete(null);
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(requestToDelete.id)}
                  disabled={deleting}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
                >
                  {deleting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <TrashIcon className="h-4 w-4" />
                      <span>Delete</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default CandidateOnboarding;
