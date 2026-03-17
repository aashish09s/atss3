import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  EnvelopeIcon, 
  BuildingOfficeIcon,
  LinkIcon,
  PaperAirplaneIcon,
  UserIcon,
  CameraIcon,
  UserGroupIcon,
  ChevronDownIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import LoadingSpinner from './LoadingSpinner';
import api from '../utils/api';
import { useClients } from '../store/clients';

const ClientEmailForm = ({ 
  isOpen, 
  onClose, 
  resume, 
  onEmailSent,
  showNotification 
}) => {
  const { clients } = useClients();
  const [formData, setFormData] = useState({
    to_emails: '',
    cc_emails: '',
    bcc_emails: '',
    subject: '',
    email_body: '',
    resume_attachment: true,
    company_logo_url: '',
    company_name: '',
    hr_name: '',
    hr_email: ''
  });
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [logoFile, setLogoFile] = useState(null);
  const [showClientDropdown, setShowClientDropdown] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [statusOptions, setStatusOptions] = useState({
    resumeSubmission: false,
    interviewSubmission: false,
    offerLetterGeneration: false,
    candidateOnboard: false
  });

  useEffect(() => {
    if (isOpen && resume) {
      fetchUserProfile();
      initializeFormData();
    }
  }, [isOpen, resume]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showClientDropdown && !event.target.closest('.client-dropdown-container')) {
        setShowClientDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showClientDropdown]);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/api/profile/');
      setUserProfile(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const initializeFormData = () => {
    const candidateName = resume.parsed_data?.full_name || resume.filename?.replace('.pdf', '') || 'Candidate';
    
    setFormData({
      to_emails: '',
      cc_emails: '',
      bcc_emails: '',
      subject: `Resume Submission - ${candidateName}`,
      email_body: generateDefaultEmailBody(candidateName, resume.parsed_data?.position || 'the position'),
      resume_attachment: true,
      company_logo_url: userProfile?.company_logo_url || '',
      company_name: userProfile?.company_name || 'Our Company',
      hr_name: userProfile?.full_name || 'HR Team',
      hr_email: userProfile?.email || ''
    });
  };

  // Update form data when user profile is fetched
  useEffect(() => {
    if (userProfile) {
      setFormData(prev => ({
        ...prev,
        company_logo_url: userProfile.company_logo_url || '',
        company_name: userProfile.company_name || 'Our Company',
        hr_name: userProfile.full_name || 'HR Team',
        hr_email: userProfile.email || ''
      }));
    }
  }, [userProfile]);

  const generateDefaultEmailBody = (candidateName, position = 'the position', currentStatusOptions = statusOptions, attachResume = formData.resume_attachment) => {
    const selectedStatuses = Object.entries(currentStatusOptions)
      .filter(([key, value]) => value)
      .map(([key]) => {
        const statusMap = {
          resumeSubmission: 'Resume Submission',
          interviewSubmission: 'Interview Submission', 
          offerLetterGeneration: 'Offer Letter Generation',
          candidateOnboard: 'Candidate Onboard'
        };
        return statusMap[key];
      });

    const statusSection = selectedStatuses.length > 0 
      ? `**Current Process Status:**
${selectedStatuses.map(status => `• ✅ ${status}`).join('\n')}

**Process Update:**
The candidate's status has been updated in our system to reflect the current stage of the hiring process.`
      : '';

    const resumeSection = attachResume 
      ? `• Resume: Attached for your review`
      : `• Resume: Available upon request`;

    const nextStepsSection = attachResume
      ? `Please review the attached resume and let me know your thoughts. If you would like to proceed with an interview or have any questions about the candidate's qualifications, please don't hesitate to reach out.`
      : `Please let me know if you would like me to send the candidate's resume. If you would like to proceed with an interview or have any questions about the candidate's qualifications, please don't hesitate to reach out.`;

    return `Dear Client,

I hope this email finds you well. I am pleased to share with you the resume of ${candidateName}, who has applied for the ${position} position.

**Candidate Overview:**
• Name: ${candidateName}
• Position Applied: ${position}
${resumeSection}

${statusSection}

**Next Steps:**
${nextStepsSection}

I am available to discuss this candidate further or provide additional information as needed.

Best regards,
${userProfile?.full_name || 'HR Team'}
${userProfile?.company_name || 'Our Company'}`;
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => {
      const newFormData = {
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      };
      
      // Update email body when attachment checkbox changes
      if (name === 'resume_attachment') {
        const candidateName = resume.parsed_data?.full_name || resume.filename?.replace('.pdf', '') || 'Candidate';
        const position = resume.parsed_data?.position || 'the position';
        const newEmailBody = generateDefaultEmailBody(candidateName, position, statusOptions, checked);
        newFormData.email_body = newEmailBody;
      }
      
      return newFormData;
    });
  };

  const handleClientSelect = (client) => {
    setSelectedClient(client);
    setFormData(prev => ({
      ...prev,
      to_emails: client.email
    }));
    setShowClientDropdown(false);
  };

  const handleRemoveSelectedClient = () => {
    setSelectedClient(null);
    setFormData(prev => ({
      ...prev,
      to_emails: ''
    }));
  };

  const handleStatusChange = (status) => {
    setStatusOptions(prev => {
      const newStatus = {
        ...prev,
        [status]: !prev[status]
      };
      
      // Update email body when status changes
      const candidateName = resume.parsed_data?.full_name || resume.filename?.replace('.pdf', '') || 'Candidate';
      const position = resume.parsed_data?.position || 'the position';
      const newEmailBody = generateDefaultEmailBody(candidateName, position, newStatus, formData.resume_attachment);
      
      setFormData(prevForm => ({
        ...prevForm,
        email_body: newEmailBody
      }));
      
      return newStatus;
    });
  };

  const handleTestEmail = async () => {
    setLoading(true);
    try {
      const response = await api.post('/api/hr/resume/test-email');
      
      if (response.data.status === 'success') {
        showNotification('Success', response.data.message, 'success');
      } else {
        showNotification('Error', response.data.message, 'error');
      }
    } catch (error) {
      console.error('Error testing email:', error);
      showNotification('Error', 'Failed to test email configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogoFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setFormData(prev => ({
          ...prev,
          company_logo_url: e.target.result
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.to_emails.trim()) {
      showNotification('Error', 'Please enter at least one recipient email address', 'error');
      return;
    }

    setLoading(true);
    try {
      const emailData = {
        ...formData,
        resume_id: resume.id,
        candidate_name: resume.parsed_data?.full_name || resume.filename?.replace('.pdf', '') || 'Candidate',
        candidate_position: resume.parsed_data?.position || 'the position',
        status_options: statusOptions
      };

      const response = await api.post('/api/hr/resume/share-with-client', emailData);
      
      // Check if there were any failed sends
      if (response.data.failed_sends && response.data.failed_sends.length > 0) {
        showNotification('Partial Success', response.data.message, 'warning');
      } else if (response.data.mock_response) {
        showNotification('Success (Mock)', response.data.message, 'success');
      } else {
        showNotification('Success', 'Resume shared with client successfully!', 'success');
      }
      
      onEmailSent();
      onClose();
    } catch (error) {
      console.error('Error sending email:', error);
      
      // Extract more specific error message
      let errorMessage = 'Failed to send email. Please try again.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showNotification('Error', errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                  <UserGroupIcon className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Share Resume with Client</h2>
                  <p className="text-blue-100 text-sm">
                    Send {resume?.parsed_data?.full_name || resume?.filename?.replace('.pdf', '') || 'candidate'} resume to clients
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Form Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Company Branding Section */}
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <BuildingOfficeIcon className="w-5 h-5 mr-2 text-blue-600" />
                  Company Branding
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Company Logo */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Company Logo
                    </label>
                    <div className="flex items-center space-x-4">
                      {formData.company_logo_url && (
                        <div className="w-16 h-16 border-2 border-gray-200 rounded-lg overflow-hidden">
                          <img
                            src={formData.company_logo_url}
                            alt="Company Logo"
                            className="w-full h-full object-contain"
                          />
                        </div>
                      )}
                      <div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleLogoUpload}
                          className="hidden"
                          id="logo-upload"
                        />
                        <label
                          htmlFor="logo-upload"
                          className="cursor-pointer inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                        >
                          <CameraIcon className="w-4 h-4 mr-2" />
                          {formData.company_logo_url ? 'Change Logo' : 'Upload Logo'}
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Company Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Name
                    </label>
                    <input
                      type="text"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Your Company Name"
                    />
                  </div>
                </div>
              </div>

              {/* Email Recipients */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <EnvelopeIcon className="w-5 h-5 mr-2 text-blue-600" />
                  Email Recipients
                </h3>

                {/* TO Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    To <span className="text-red-500">*</span>
                  </label>
                  
                  {/* Client Selection Dropdown */}
                  <div className="relative mb-3 client-dropdown-container">
                    <button
                      type="button"
                      onClick={() => setShowClientDropdown(!showClientDropdown)}
                      className="w-full flex items-center justify-between px-3 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <span className="text-sm text-gray-500">
                        {selectedClient ? `${selectedClient.name} (${selectedClient.email})` : 'Select from existing clients...'}
                      </span>
                      <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                    </button>
                    
                    {showClientDropdown && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        {clients.length > 0 ? (
                          clients.map((client) => (
                            <button
                              key={client.id}
                              type="button"
                              onClick={() => handleClientSelect(client)}
                              className="w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                            >
                              <div className="font-medium text-gray-900">{client.name}</div>
                              <div className="text-sm text-gray-500">{client.email}</div>
                              <div className="text-xs text-gray-400">{client.company}</div>
                            </button>
                          ))
                        ) : (
                          <div className="px-3 py-2 text-sm text-gray-500">
                            No clients available. Create clients first.
                          </div>
                        )}
                      </div>
                    )}
                    
                    {selectedClient && (
                      <div className="mt-2 flex items-center justify-between p-2 bg-blue-50 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <UserIcon className="w-4 h-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-900">
                            {selectedClient.name} ({selectedClient.email})
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={handleRemoveSelectedClient}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {/* Manual Email Input */}
                  <input
                    type="email"
                    name="to_emails"
                    value={formData.to_emails}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="client@company.com, another@company.com"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Select from existing clients above or enter email addresses manually (separate multiple with commas)
                  </p>
                </div>

                {/* CC Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CC (Optional)
                  </label>
                  <input
                    type="email"
                    name="cc_emails"
                    value={formData.cc_emails}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="manager@company.com, team@company.com"
                  />
                </div>

                {/* BCC Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    BCC (Optional)
                  </label>
                  <input
                    type="email"
                    name="bcc_emails"
                    value={formData.bcc_emails}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="hr@company.com, backup@company.com"
                  />
                </div>
              </div>

              {/* Email Content */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <PaperAirplaneIcon className="w-5 h-5 mr-2 text-blue-600" />
                  Email Content
                </h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subject
                  </label>
                  <input
                    type="text"
                    name="subject"
                    value={formData.subject}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Resume Submission - [Candidate Name]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Body
                  </label>
                  <textarea
                    name="email_body"
                    value={formData.email_body}
                    onChange={handleInputChange}
                    rows={12}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                    placeholder="Write your email message..."
                  />
                </div>

                {/* Resume Attachment Option */}
                <div className={`flex items-center space-x-3 p-4 rounded-lg transition-colors ${
                  formData.resume_attachment ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
                }`}>
                  <input
                    type="checkbox"
                    name="resume_attachment"
                    checked={formData.resume_attachment}
                    onChange={handleInputChange}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <div>
                    <label className={`text-sm font-medium ${
                      formData.resume_attachment ? 'text-green-700' : 'text-gray-700'
                    }`}>
                      Attach Resume File
                      {formData.resume_attachment && (
                        <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                          ✓ PDF will be attached
                        </span>
                      )}
                    </label>
                    <p className={`text-xs ${
                      formData.resume_attachment ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {formData.resume_attachment 
                        ? 'The candidate\'s resume will be included as a PDF attachment'
                        : 'The candidate\'s resume will not be attached to this email'
                      }
                    </p>
                  </div>
                </div>
              </div>

              {/* Status Options */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <CheckCircleIcon className="w-5 h-5 mr-2 text-blue-600" />
                  Process Status Options
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="resumeSubmission"
                      checked={statusOptions.resumeSubmission}
                      onChange={() => handleStatusChange('resumeSubmission')}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="resumeSubmission" className="text-sm font-medium text-gray-700">
                      Resume Submission
                    </label>
                  </div>

                  <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="interviewSubmission"
                      checked={statusOptions.interviewSubmission}
                      onChange={() => handleStatusChange('interviewSubmission')}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="interviewSubmission" className="text-sm font-medium text-gray-700">
                      Interview Submission
                    </label>
                  </div>

                  <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="offerLetterGeneration"
                      checked={statusOptions.offerLetterGeneration}
                      onChange={() => handleStatusChange('offerLetterGeneration')}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="offerLetterGeneration" className="text-sm font-medium text-gray-700">
                      Offer Letter Generation
                    </label>
                  </div>

                  <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                    <input
                      type="checkbox"
                      id="candidateOnboard"
                      checked={statusOptions.candidateOnboard}
                      onChange={() => handleStatusChange('candidateOnboard')}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="candidateOnboard" className="text-sm font-medium text-gray-700">
                      Candidate Onboard
                    </label>
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-700">
                    <strong>Note:</strong> Selected status options will be included in the email to help clients understand the current process stage.
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={handleTestEmail}
                  disabled={loading}
                  className="px-4 py-2 text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <EnvelopeIcon className="w-4 h-4" />
                  <span>Test Email Config</span>
                </button>
                
                <div className="flex items-center space-x-4">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-6 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {loading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Sending...</span>
                      </>
                    ) : (
                      <>
                        <PaperAirplaneIcon className="w-4 h-4" />
                        <span>Send Email</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ClientEmailForm;
