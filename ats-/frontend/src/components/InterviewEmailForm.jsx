import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  EnvelopeIcon, 
  BuildingOfficeIcon,
  LinkIcon,
  PaperAirplaneIcon,
  UserIcon,
  CameraIcon
} from '@heroicons/react/24/outline';
import LoadingSpinner from './LoadingSpinner';
import api from '../utils/api';

const InterviewEmailForm = ({ 
  isOpen, 
  onClose, 
  resume, 
  onEmailSent,
  showNotification 
}) => {
  const [formData, setFormData] = useState({
    candidate_email: '',
    candidate_name: '',
    position: '',  // Added missing position field
    subject: '',
    email_body: '',
    virtual_interview_link: '',
    company_logo_url: '',
    company_name: '',
    hr_name: '',
    hr_email: ''
  });
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [logoFile, setLogoFile] = useState(null);

  useEffect(() => {
    if (isOpen && resume) {
      fetchUserProfile();
      initializeFormData();
    }
  }, [isOpen, resume]);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/api/profile/');
      setUserProfile(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const initializeFormData = () => {
    const candidateName = resume.parsed_data?.name || resume.parsed_data?.candidate_name || 'Candidate';
    const candidateEmail = resume.parsed_data?.email || '';
    
    setFormData({
      candidate_email: candidateEmail,
      candidate_name: candidateName,
      position: resume.parsed_data?.position || '',
      subject: `Interview Invitation - ${candidateName}`,
      email_body: generateDefaultEmailBody(candidateName, resume.parsed_data?.position || 'the position'),
      virtual_interview_link: '',
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
        hr_email: userProfile.email || '',
        position: prev.position // Keep existing position
      }));
    }
  }, [userProfile]);

  const generateDefaultEmailBody = (candidateName, position = 'the position') => {
    return `Dear ${candidateName},

Thank you for your interest in joining our team for the ${position} role. We have reviewed your resume and are impressed with your qualifications and experience.

We would like to invite you for an interview to discuss your background, skills, and how you can contribute to our organization.

**Interview Details:**
• Date: [To be scheduled based on your availability]
• Duration: Approximately 45-60 minutes
• Format: [In-person/Virtual - to be confirmed]

**What to Expect:**
• Discussion about your experience and skills
• Questions about your career goals and motivation
• Opportunity for you to ask questions about the role and company
• Discussion about next steps

Please let us know your availability for the coming week, and we will schedule the interview at a convenient time for you.

If you have any questions or need to reschedule, please don't hesitate to contact us.

Best regards,
HR Team`;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogoFile(file);
      // Create a preview URL
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
    setLoading(true);

    try {
      // If there's a new logo file, upload it first
      let finalLogoUrl = formData.company_logo_url;
      if (logoFile) {
        const logoFormData = new FormData();
        logoFormData.append('file', logoFile);
        
        const logoResponse = await api.post('/api/profile/upload-company-logo', logoFormData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        finalLogoUrl = logoResponse.data.file_url;
      }

      // Send the interview email
      await api.post('/api/hr/resume/send-interview-email', {
        resume_id: resume.id,
        candidate_email: formData.candidate_email,
        candidate_name: formData.candidate_name,
        subject: formData.subject,
        email_body: formData.email_body,
        virtual_interview_link: formData.virtual_interview_link,
        company_logo_url: finalLogoUrl,
        company_name: formData.company_name,
        hr_name: formData.hr_name,
        hr_email: formData.hr_email,
        position: formData.position // Add position to submission
      });

      showNotification('Success', 'Interview email sent successfully!', 'success');
      onEmailSent();
      onClose();
    } catch (error) {
      console.error('Error sending interview email:', error);
      showNotification('Error', 'Failed to send interview email', 'error');
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
        className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                  <EnvelopeIcon className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold">Send Interview Email</h2>
                  <p className="text-blue-100">Invite candidate for an interview</p>
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
              {/* Company Logo Section */}
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
                      <div className="relative">
                        <div className="w-20 h-20 rounded-lg bg-white border-2 border-gray-200 flex items-center justify-center overflow-hidden">
                          {formData.company_logo_url ? (
                            <img 
                              src={formData.company_logo_url} 
                              alt="Company Logo" 
                              className="w-full h-full object-contain"
                            />
                          ) : (
                            <BuildingOfficeIcon className="w-10 h-10 text-gray-400" />
                          )}
                        </div>
                        <label className="absolute bottom-0 right-0 bg-blue-500 text-white p-1.5 rounded-full cursor-pointer hover:bg-blue-600 transition-colors">
                          <CameraIcon className="w-3 h-3" />
                          <input 
                            type="file" 
                            accept="image/*" 
                            onChange={handleLogoChange}
                            className="hidden"
                          />
                        </label>
                      </div>
                      <div className="flex-1">
                        <input
                          type="text"
                          name="company_name"
                          value={formData.company_name}
                          onChange={handleInputChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Company Name"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Upload a logo or use existing one from profile
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* HR Information */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        HR Representative Name
                      </label>
                      <input
                        type="text"
                        name="hr_name"
                        value={formData.hr_name}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Your Name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        HR Email
                      </label>
                      <input
                        type="email"
                        name="hr_email"
                        value={formData.hr_email}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="your.email@company.com"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Candidate Information */}
              <div className="bg-blue-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <UserIcon className="w-5 h-5 mr-2 text-blue-600" />
                  Candidate Information
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Candidate Name
                    </label>
                    <input
                      type="text"
                      name="candidate_name"
                      value={formData.candidate_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Candidate Name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Candidate Email
                    </label>
                    <input
                      type="email"
                      name="candidate_email"
                      value={formData.candidate_email}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="candidate@email.com"
                    />
                  </div>
                </div>
                
                {/* Position Field */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Position Applied For
                  </label>
                  <input
                    type="text"
                    name="position"
                    value={formData.position}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Software Engineer, Marketing Manager"
                  />
                </div>
              </div>

              {/* Email Content */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Subject
                  </label>
                  <input
                    type="text"
                    name="subject"
                    value={formData.subject}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Interview Invitation - [Candidate Name]"
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
                    placeholder="Write your interview invitation email..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                    <LinkIcon className="w-4 h-4 mr-2 text-blue-600" />
                    Virtual Interview Link (Optional)
                  </label>
                  <input
                    type="url"
                    name="virtual_interview_link"
                    value={formData.virtual_interview_link}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="https://meet.google.com/xxx-xxxx-xxx or Zoom link"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Add a meeting link if this will be a virtual interview
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all font-medium flex items-center space-x-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Sending...</span>
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="w-4 h-4" />
                      <span>Send Interview Email</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default InterviewEmailForm;
