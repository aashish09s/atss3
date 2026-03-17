import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  UserIcon, 
  EnvelopeIcon, 
  PhoneIcon,
  MapPinIcon,
  AcademicCapIcon,
  DocumentTextIcon,
  PhotoIcon,
  CreditCardIcon,
  IdentificationIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';

const CandidateOnboardingForm = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [onboardingData, setOnboardingData] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    personalDetails: {
      fullName: '',
      email: '',
      phone: '',
      dateOfBirth: '',
      address: '',
      city: '',
      state: '',
      pincode: ''
    },
    documents: {
      photo: null,
      resume: null,
      degree: null,
      aadharCard: null,
      panCard: null,
      idProof: null,
      bankDetails: null
    }
  });

  useEffect(() => {
    validateToken();
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await api.get(`/api/candidate-onboarding/validate/${token}`);
      setOnboardingData(response.data);
      setTokenValid(true);
      
      // Pre-fill form with existing data if any
      if (response.data.candidate_details) {
        setFormData(prev => ({
          ...prev,
          personalDetails: {
            ...prev.personalDetails,
            ...response.data.candidate_details.personal_details
          }
        }));
      }
    } catch (error) {
      console.error('Token validation failed:', error);
      setTokenValid(false);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (field, file) => {
    setFormData(prev => ({
      ...prev,
      documents: {
        ...prev.documents,
        [field]: file
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const formDataToSend = new FormData();
      
      // Add personal details with correct field names for backend
      formDataToSend.append('personal_details_full_name', formData.personalDetails.fullName);
      formDataToSend.append('personal_details_email', formData.personalDetails.email);
      formDataToSend.append('personal_details_phone', formData.personalDetails.phone);
      formDataToSend.append('personal_details_date_of_birth', formData.personalDetails.dateOfBirth);
      formDataToSend.append('personal_details_address', formData.personalDetails.address);
      formDataToSend.append('personal_details_city', formData.personalDetails.city);
      formDataToSend.append('personal_details_state', formData.personalDetails.state);
      formDataToSend.append('personal_details_pincode', formData.personalDetails.pincode);

      // Add documents with correct field names for backend
      if (formData.documents.photo) {
        formDataToSend.append('documents_photo', formData.documents.photo);
      }
      if (formData.documents.resume) {
        formDataToSend.append('documents_resume', formData.documents.resume);
      }
      if (formData.documents.degree) {
        formDataToSend.append('documents_degree', formData.documents.degree);
      }
      if (formData.documents.aadharCard) {
        formDataToSend.append('documents_aadhar_card', formData.documents.aadharCard);
      }
      if (formData.documents.panCard) {
        formDataToSend.append('documents_pan_card', formData.documents.panCard);
      }
      if (formData.documents.idProof) {
        formDataToSend.append('documents_id_proof', formData.documents.idProof);
      }
      if (formData.documents.bankDetails) {
        formDataToSend.append('documents_bank_details', formData.documents.bankDetails);
      }

      await api.post(`/api/candidate-onboarding/submit/${token}`, formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      alert('Onboarding details submitted successfully!');
      navigate('/onboarding-success');
    } catch (error) {
      console.error('Error submitting onboarding:', error);
      alert('Failed to submit onboarding details. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Validating your invitation...</p>
        </div>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invalid or Expired Link</h1>
          <p className="text-gray-600">This onboarding link is invalid or has expired. Please contact HR for a new invitation.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to {onboardingData?.company_name}</h1>
          <p className="mt-2 text-gray-600">
            Please complete your onboarding by filling out the form below
          </p>
          <div className="mt-4 inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full">
            <CheckCircleIcon className="h-5 w-5 mr-2" />
            <span className="text-sm font-medium">Position: {onboardingData?.position}</span>
          </div>
        </div>

        {/* Onboarding Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-8"
        >
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Personal Details Section */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <UserIcon className="h-6 w-6 mr-2 text-blue-600" />
                Personal Details
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    value={formData.personalDetails.fullName}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        fullName: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={formData.personalDetails.email}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        email: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    value={formData.personalDetails.phone}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        phone: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date of Birth *
                  </label>
                  <input
                    type="date"
                    value={formData.personalDetails.dateOfBirth}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        dateOfBirth: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Address *
                  </label>
                  <input
                    type="text"
                    value={formData.personalDetails.address}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        address: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    City *
                  </label>
                  <input
                    type="text"
                    value={formData.personalDetails.city}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        city: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    State *
                  </label>
                  <input
                    type="text"
                    value={formData.personalDetails.state}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        state: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    PIN Code *
                  </label>
                  <input
                    type="text"
                    value={formData.personalDetails.pincode}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      personalDetails: {
                        ...prev.personalDetails,
                        pincode: e.target.value
                      }
                    }))}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Documents Section */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <DocumentTextIcon className="h-6 w-6 mr-2 text-blue-600" />
                Required Documents
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <PhotoIcon className="h-5 w-5 inline mr-2" />
                    Profile Photo *
                  </label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileChange('photo', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <DocumentTextIcon className="h-5 w-5 inline mr-2" />
                    Resume/CV *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => handleFileChange('resume', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <AcademicCapIcon className="h-5 w-5 inline mr-2" />
                    Degree Certificate *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileChange('degree', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <IdentificationIcon className="h-5 w-5 inline mr-2" />
                    Aadhar Card *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileChange('aadharCard', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <IdentificationIcon className="h-5 w-5 inline mr-2" />
                    PAN Card *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileChange('panCard', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <IdentificationIcon className="h-5 w-5 inline mr-2" />
                    ID Proof *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileChange('idProof', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <CreditCardIcon className="h-5 w-5 inline mr-2" />
                    Bank Details *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileChange('bankDetails', e.target.files[0])}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-6">
              <button
                type="submit"
                disabled={submitting}
                className="w-full btn-gradient-primary py-3 px-6 rounded-lg font-medium text-lg disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Submit Onboarding Details'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
};

export default CandidateOnboardingForm;
