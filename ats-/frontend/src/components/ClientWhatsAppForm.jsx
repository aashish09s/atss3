import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  PhoneIcon, 
  BuildingOfficeIcon,
  LinkIcon,
  PaperAirplaneIcon,
  UserIcon,
  CameraIcon,
  UserGroupIcon,
  ChevronDownIcon,
  CheckCircleIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import LoadingSpinner from './LoadingSpinner';
import api from '../utils/api';
import { useClients } from '../store/clients';

const ClientWhatsAppForm = ({ 
  isOpen, 
  onClose, 
  resume, 
  onWhatsAppSent,
  showNotification 
}) => {
  const { clients } = useClients();
  const [formData, setFormData] = useState({
    to_phones: '',
    candidate_name: '',
    candidate_position: '',
    company_name: '',
    hr_name: '',
    hr_phone: '',
    additional_message: '',
    resume_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [showClientDropdown, setShowClientDropdown] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);

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
      const response = await api.get('/api/hr/me');
      setUserProfile(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const initializeFormData = () => {
    if (resume && userProfile) {
      setFormData({
        to_phones: '',
        candidate_name: resume.parsed_data?.full_name || resume.filename?.replace('.pdf', '') || 'Candidate',
        candidate_position: resume.parsed_data?.position || 'the position',
        company_name: userProfile.company_name || '',
        hr_name: userProfile.full_name || '',
        hr_phone: userProfile.phone || '',
        additional_message: '',
        resume_url: ''
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleClientSelect = (client) => {
    setSelectedClient(client);
    setFormData(prev => ({
      ...prev,
      to_phones: client.phone || '',
      company_name: client.company_name || prev.company_name
    }));
    setShowClientDropdown(false);
  };

  const validatePhoneNumber = (phone) => {
    // Basic phone validation - remove all non-digit characters and check length
    const cleanPhone = phone.replace(/\D/g, '');
    return cleanPhone.length >= 7 && cleanPhone.length <= 15;
  };

  const formatPhoneNumber = (phone) => {
    // Remove all non-digit characters
    const cleanPhone = phone.replace(/\D/g, '');
    
    // If it's a 10-digit number, assume it's US and add country code
    if (cleanPhone.length === 10) {
      return '1' + cleanPhone;
    }
    
    return cleanPhone;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.to_phones.trim()) {
      showNotification('Error', 'Please enter at least one recipient phone number', 'error');
      return;
    }

    // Validate phone numbers
    const phoneNumbers = formData.to_phones.split(',').map(phone => phone.trim());
    for (const phone of phoneNumbers) {
      if (!validatePhoneNumber(phone)) {
        showNotification('Error', `Invalid phone number format: ${phone}`, 'error');
        return;
      }
    }

    setLoading(true);
    try {
      const whatsappData = {
        ...formData,
        resume_id: resume.id,
        to_phones: formData.to_phones,
        resume_url: formData.resume_url || `${window.location.origin}/api/hr/resume/download/${resume.id}`
      };

      const response = await api.post('/api/hr/resume/share-with-client-whatsapp', whatsappData);
      
      // Check if there were any failed sends
      if (response.data.failed_sends && response.data.failed_sends.length > 0) {
        showNotification('Partial Success', response.data.message, 'warning');
      } else {
        showNotification('Success', 'Resume shared with client via WhatsApp successfully!', 'success');
      }
      
      onWhatsAppSent();
      onClose();
    } catch (error) {
      console.error('Error sending WhatsApp message:', error);
      
      // Extract more specific error message
      let errorMessage = 'Failed to send WhatsApp message. Please try again.';
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
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                  <ChatBubbleLeftRightIcon className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Share Resume via WhatsApp</h2>
                  <p className="text-green-100 text-sm">
                    Send {resume?.parsed_data?.full_name || resume?.filename?.replace('.pdf', '') || 'candidate'} resume to clients via WhatsApp
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
              {/* Recipients */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-gray-700">
                    Recipient Phone Numbers
                  </label>
                  <div className="relative client-dropdown-container">
                    <button
                      type="button"
                      onClick={() => setShowClientDropdown(!showClientDropdown)}
                      className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors"
                    >
                      <UserGroupIcon className="w-4 h-4" />
                      <span>Select Client</span>
                      <ChevronDownIcon className="w-4 h-4" />
                    </button>
                    
                    {showClientDropdown && (
                      <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-10 max-h-48 overflow-y-auto">
                        {clients.length > 0 ? (
                          clients.map((client) => (
                            <button
                              key={client.id}
                              type="button"
                              onClick={() => handleClientSelect(client)}
                              className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm"
                            >
                              <div className="font-medium text-gray-900">{client.name}</div>
                              <div className="text-gray-500">{client.company_name}</div>
                              <div className="text-gray-500">{client.phone}</div>
                            </button>
                          ))
                        ) : (
                          <div className="px-4 py-2 text-sm text-gray-500">No clients available</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                <textarea
                  name="to_phones"
                  value={formData.to_phones}
                  onChange={handleInputChange}
                  placeholder="Enter phone numbers separated by commas (e.g., +1234567890, +9876543210)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  rows={2}
                  required
                />
                <p className="text-xs text-gray-500">
                  Include country code (e.g., +1 for US, +91 for India)
                </p>
              </div>

              {/* Candidate Information */}
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Position
                  </label>
                  <input
                    type="text"
                    name="candidate_position"
                    value={formData.candidate_position}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    required
                  />
                </div>
              </div>

              {/* Company Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    name="company_name"
                    value={formData.company_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    HR Phone Number
                  </label>
                  <input
                    type="tel"
                    name="hr_phone"
                    value={formData.hr_phone}
                    onChange={handleInputChange}
                    placeholder="+1234567890"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    required
                  />
                </div>
              </div>

              {/* HR Information */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  HR Name
                </label>
                <input
                  type="text"
                  name="hr_name"
                  value={formData.hr_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  required
                />
              </div>

              {/* Additional Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Message (Optional)
                </label>
                <textarea
                  name="additional_message"
                  value={formData.additional_message}
                  onChange={handleInputChange}
                  placeholder="Add any additional notes or instructions..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  rows={3}
                />
              </div>

              {/* Resume URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Resume URL (Optional)
                </label>
                <input
                  type="url"
                  name="resume_url"
                  value={formData.resume_url}
                  onChange={handleInputChange}
                  placeholder="Leave empty to use default resume download link"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>

              {/* Submit Button */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center space-x-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <ChatBubbleLeftRightIcon className="w-4 h-4" />
                  )}
                  <span>{loading ? 'Sending...' : 'Send via WhatsApp'}</span>
                </button>
              </div>
            </form>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ClientWhatsAppForm;
