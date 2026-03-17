import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { DocumentTextIcon, PlusIcon, EyeIcon, XMarkIcon, UserIcon, StarIcon, CheckCircleIcon, XCircleIcon, DocumentArrowDownIcon, TrashIcon } from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import ResumeDetailView from '../../components/ResumeDetailView';
import AILoadingSpinner from '../../components/AILoadingSpinner';
import LoadingSpinner from '../../components/LoadingSpinner';
import api from '../../utils/api';

const JDManager = () => {
  const [jds, setJds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [jdsLoading, setJdsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description_text: '',
    client_name: '',
    budget_amount: '',
    your_earning: '',
    is_active: true
  });
  const [parsedResult, setParsedResult] = useState(null);
  const [selectedJD, setSelectedJD] = useState(null);
  const [matchedResumes, setMatchedResumes] = useState([]);

  const [matchesLoading, setMatchesLoading] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [showMatchedResumes, setShowMatchedResumes] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [jdToDelete, setJdToDelete] = useState(null);

  useEffect(() => {
    fetchJDs();
  }, []);

  const fetchJDs = async () => {
    try {
      setJdsLoading(true);
      const response = await api.get('/api/hr/jds/');
      setJds(response.data || []);
      // const jdData = Array.isArray(response.data)
      // ? response.data
      // : (response.data?.jds || response.data?.data || response.data?.items || []);
      // setJds(jdData);

    } catch (error) {
      console.error('Error fetching JDs:', error);
      setJds([]); // Set empty array on error to prevent infinite loading
      alert('Failed to load job descriptions. Please try again.');
    } finally {
      setJdsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Validate title (min 3 chars)
    if (!formData.title || formData.title.trim().length < 3) {
      alert("Job Title must be at least 3 characters.");
      setLoading(false);
      return;
    }

    // Validate minimum 3 digits for budget and earning
    if (!formData.budget_amount || formData.budget_amount.length < 3 || !formData.your_earning || formData.your_earning.length < 3) {
      alert("Total Budget and Your Earning must be at least 3 digits (minimum ₹100).");
      setLoading(false);
      return;
    }

    // Validate client_name (required, not empty)
    if (!formData.client_name || formData.client_name.trim().length === 0) {
      alert("Client Name is required.");
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/api/hr/jds/', formData);
      setParsedResult(response.data);
      setFormData({ 
        title: '', 
        description_text: '',
        client_name: '',
        budget_amount: '',
        your_earning: '',
        is_active: true
      });
      setShowCreateForm(false);
      fetchJDs(); // Refresh the list
    } catch (error) {
      console.error('Error creating JD:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // Validate budget_amount and your_earning to max 7 digits
    if ((name === 'budget_amount' || name === 'your_earning') && type === 'number') {
      // Remove any non-digit characters
      const numericValue = value.replace(/\D/g, '');
      
      // Limit to 7 digits
      if (numericValue.length > 7) {
        return; // Don't update if exceeds 7 digits
      }
      
      setFormData(prev => ({
        ...prev,
        [name]: numericValue
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleViewJD = (jd) => {
    setSelectedJD(jd);
  };



  const handleViewMatchedResumes = async (jd) => {
    setSelectedJD(jd);
    setShowMatchedResumes(true);
    setMatchesLoading(true);
    
    try {
      console.log(`Starting resume matching for JD: ${jd.title}`);
      const startTime = Date.now();
      
      const response = await api.get(`/api/hr/jds/${jd.id}/matches`);
      const endTime = Date.now();
      const processingTime = (endTime - startTime) / 1000;
      
      console.log(`Resume matching completed in ${processingTime.toFixed(2)} seconds`);
      console.log(`Found ${response.data.length} matches`);
      
      setMatchedResumes(response.data);
    } catch (error) {
      console.error('Error fetching matched resumes:', error);
      setMatchedResumes([]);
    } finally {
      setMatchesLoading(false);
    }
  };

  const handleViewResume = async (resumeId) => {
    try {
      // Clean resume ID - remove any trailing characters
      const cleanResumeId = resumeId?.toString().trim().split(':')[0] || resumeId;
      console.log('Fetching resume with ID:', cleanResumeId);
      const response = await api.get(`/api/hr/resumes/${cleanResumeId}`);
      setSelectedResume(response.data);
    } catch (error) {
      console.error('Error fetching resume details:', error);
      console.error('Resume ID that failed:', resumeId);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load resume details.';
      alert(`Failed to load resume details: ${errorMessage}`);
    }
  };

  const closeModal = () => {
    setShowCreateForm(false);
    setShowMatchedResumes(false);
    setSelectedResume(null);
    setSelectedJD(null);
    setMatchedResumes([]);
    setShowDeleteConfirm(false);
    setJdToDelete(null);
  };

  const closeResumeModal = () => {
    setSelectedResume(null);
  };

  const handleDownloadResume = async (resumeId) => {
    try {
      // First, get the resume details to get the filename
      const resumeResponse = await api.get(`/api/hr/resumes/${resumeId}`);
      const resume = resumeResponse.data;
      
      // Download the file using the correct endpoint
      const response = await api.get(`/api/hr/resume/download/${resumeId}`, { 
        responseType: 'blob' 
      });
      
      // Create blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', resume.filename || `resume_${resumeId}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading resume:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to download resume.';
      alert(errorMessage);
    }
  };

  const handleDeleteJD = async (jd) => {
    setJdToDelete(jd);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteJD = async () => {
    if (!jdToDelete) return;
    
    try {
      await api.delete(`/api/hr/jds/${jdToDelete.id}`);
      setShowDeleteConfirm(false);
      setJdToDelete(null);
      fetchJDs(); // Refresh the list
      alert('Job Description deleted successfully!');
    } catch (error) {
      console.error('Error deleting JD:', error);
      alert('Failed to delete Job Description.');
    }
  };

  const cancelDeleteJD = () => {
    setShowDeleteConfirm(false);
    setJdToDelete(null);
  };

  return (
    <div className="p-6">
      <Header 
        title="Job Description Manager" 
        subtitle="Create and manage job descriptions with AI parsing"
      />

      <div className="mt-6 space-y-6">
        {/* Create JD Button */}
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Job Descriptions</h3>
          <button
            onClick={() => setShowCreateForm(true)}
            className="btn-gradient-primary px-4 py-2 rounded-lg font-medium flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create JD</span>
          </button>
        </div>

        {/* Create Form Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Create Job Description</h3>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Title
                    </label>
                    <input
                      type="text"
                      name="title"
                      value={formData.title}
                      onChange={handleChange}
                      maxLength="30"
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g. Senior React Developer"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Description
                    </label>
                    <textarea
                      name="description_text"
                      value={formData.description_text}
                      onChange={handleChange}
                      required
                      rows={12}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Paste the complete job description here..."
                    />
                  </div>

                  {/* Client Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Client Name
                    </label>
                    <input
                      type="text"
                      name="client_name"
                      value={formData.client_name}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g. ABC Technologies Pvt Ltd"
                    />
                  </div>

                  {/* Total Budget (INR) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Total Budget for Position (₹ Indian Rupees) <span className="text-xs text-gray-500">(Max 7 digits)</span>
                    </label>
                    <input
                      type="text"
                      name="budget_amount"
                      value={formData.budget_amount}
                      onChange={handleChange}
                      max={9999999}
                      maxLength={7}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g. 1000000"
                    />
                    {formData.budget_amount && formData.budget_amount.length > 7 && (
                      <p className="text-xs text-red-500 mt-1">Maximum 7 digits allowed</p>
                    )}
                  </div>

                  {/* Your Earning (INR) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Your Earning (₹ Indian Rupees) <span className="text-xs text-gray-500">(Max 7 digits)</span>
                    </label>
                    <input
                      type="text"
                      name="your_earning"
                      value={formData.your_earning}
                      onChange={handleChange}
                      max={9999999}
                      maxLength={7}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="e.g. 500000"
                    />
                    {formData.your_earning && formData.your_earning.length > 7 && (
                      <p className="text-xs text-red-500 mt-1">Maximum 7 digits allowed</p>
                    )}
                  </div>

                  {/* Active Status */}
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleChange}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Mark this position as active (currently hiring)
                    </label>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="btn-gradient-primary px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                    >
                      {loading ? 'Processing...' : 'Create & Parse'}
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </div>
        )}

        {/* Parsed Result Display */}
        {parsedResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border border-green-200 rounded-lg p-6"
          >
            <h4 className="font-medium text-green-900 mb-4">✅ JD Created & Parsed Successfully</h4>
            
            {parsedResult.parsed_jd && (
              <div className="bg-white rounded-lg p-4 space-y-3">
                <div>
                  <span className="font-medium text-gray-700">Title:</span>
                  <span className="ml-2">{parsedResult.parsed_jd.title}</span>
                </div>
                
                {parsedResult.parsed_jd.skills && (
                  <div>
                    <span className="font-medium text-gray-700">Required Skills:</span>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {parsedResult.parsed_jd.skills.map((skill, index) => (
                        <span
                          key={index}
                          className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {parsedResult.parsed_jd.requirements && (
                  <div>
                    <span className="font-medium text-gray-700">Key Requirements:</span>
                    <ul className="mt-1 text-sm text-gray-600">
                      {parsedResult.parsed_jd.requirements.slice(0, 3).map((req, index) => (
                        <li key={index} className="ml-4">• {req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* JDs List */}
        {jdsLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner 
              size="lg" 
              message="Loading job descriptions..."
            />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {jds.map((jd) => (
                <motion.div
                  key={jd.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-xl shadow-sm p-6 card-hover"
                >
                  <div className="flex items-start justify-between mb-4 gap-4">
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <DocumentTextIcon className="h-8 w-8 text-blue-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-semibold text-gray-900 truncate">{jd.title}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 ${
                            jd.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {jd.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        {jd.jd_unique_id && (
                          <p className="text-xs text-gray-400 font-mono truncate">
                            ID: {jd.jd_unique_id}
                          </p>
                        )}
                        {jd.client_name && (
                          <p className="text-sm text-gray-600 font-medium truncate">
                            Client: {jd.client_name}
                          </p>
                        )}
                        <p className="text-sm text-gray-500">
                          Created {new Date(jd.created_at).toLocaleDateString()}
                        </p>
                        {(jd.budget_amount || jd.your_earning) && (
                          <div className="space-y-1 mt-1">
                            {jd.budget_amount && (
                              <p className="text-sm text-blue-600 font-medium truncate" title={`Budget: ₹${jd.budget_amount.toLocaleString('en-IN')}`}>
                                Budget: ₹{jd.budget_amount.toLocaleString('en-IN')}
                              </p>
                            )}
                            {jd.your_earning && (
                              <p className="text-sm text-green-600 font-medium truncate" title={`Earning: ₹${jd.your_earning.toLocaleString('en-IN')}`}>
                                Earning: ₹{jd.your_earning.toLocaleString('en-IN')}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <button 
                        onClick={() => handleViewJD(jd)}
                        className="text-gray-400 hover:text-gray-600 transition-colors p-1"
                        title="View JD Details"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                      <button 
                        onClick={() => handleDeleteJD(jd)}
                        className="text-red-400 hover:text-red-600 transition-colors p-1"
                        title="Delete JD"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>

                  {jd.parsed_jd && (
                    <div className="space-y-3">
                      {jd.parsed_jd.skills && (
                        <div>
                          <span className="text-sm font-medium text-gray-700">Skills:</span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {jd.parsed_jd.skills.slice(0, 4).map((skill, index) => (
                              <span
                                key={index}
                                className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
                              >
                                {skill}
                              </span>
                            ))}
                            {jd.parsed_jd.skills.length > 4 && (
                              <span className="text-xs text-gray-500">
                                +{jd.parsed_jd.skills.length - 4} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="pt-3 border-t border-gray-100">
                        <button 
                          onClick={() => handleViewMatchedResumes(jd)}
                          disabled={matchesLoading}
                          className="text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          {matchesLoading ? 'Loading...' : 'View Matched Resumes →'}
                        </button>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>

            {jds.length === 0 && (
              <div className="text-center py-12">
                <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Job Descriptions</h3>
                <p className="text-gray-500 mb-6">Create your first JD to get started with AI-powered parsing</p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="btn-gradient-primary px-6 py-3 rounded-lg font-medium"
                >
                  Create First JD
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* JD Detail Modal */}
      {selectedJD && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <h2 className="text-xl font-semibold text-gray-900">{selectedJD.title}</h2>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    selectedJD.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedJD.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                {selectedJD.jd_unique_id && (
                  <p className="text-xs text-gray-400 font-mono mb-1">
                    JD ID: {selectedJD.jd_unique_id}
                  </p>
                )}
                {selectedJD.client_name && (
                  <p className="text-sm text-gray-600 font-medium mb-1">
                    Client: {selectedJD.client_name}
                  </p>
                )}
                {(selectedJD.budget_amount || selectedJD.your_earning) && (
                  <div className="flex items-center space-x-4 mb-1">
                    {selectedJD.budget_amount && (
                      <p className="text-sm text-blue-600 font-medium">
                        Budget: ₹{selectedJD.budget_amount.toLocaleString('en-IN')}
                      </p>
                    )}
                    {selectedJD.your_earning && (
                      <p className="text-sm text-green-600 font-medium">
                        Earning: ₹{selectedJD.your_earning.toLocaleString('en-IN')}
                      </p>
                    )}
                  </div>
                )}
                <p className="text-sm text-gray-500">
                  Created {new Date(selectedJD.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[70vh]">
              <div className="space-y-6">
                {/* Job Description */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Job Description</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {selectedJD.description_text}
                    </p>
                  </div>
                </div>

                {/* Parsed Information */}
                {selectedJD.parsed_jd && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Parsed Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selectedJD.parsed_jd.skills && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Required Skills</h4>
                          <div className="flex flex-wrap gap-2">
                            {selectedJD.parsed_jd.skills.map((skill, index) => (
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

                      {selectedJD.parsed_jd.experience && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Experience Level</h4>
                          <p className="text-gray-700">{selectedJD.parsed_jd.experience}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-between items-center p-6 border-t border-gray-200">
              <div className="flex space-x-3">
                <button
                  onClick={() => handleViewMatchedResumes(selectedJD)}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  View Matched Resumes
                </button>
                <button
                  onClick={() => handleDeleteJD(selectedJD)}
                  className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  Delete JD
                </button>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Matched Resumes Modal */}
      {showMatchedResumes && selectedJD && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Matched Resumes for "{selectedJD.title}"
                  </h2>
                  <p className="text-gray-500">
                    {matchesLoading ? 'AI is analyzing resumes...' : `${matchedResumes.length} resumes found with matching scores`}
                  </p>
                </div>
                <button
                  onClick={() => setShowMatchedResumes(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                {matchesLoading ? (
                  <AILoadingSpinner 
                    size="lg"
                    message="🚀 Our optimized AI is analyzing resumes with concurrent processing for maximum speed. This should be much faster now!"
                  />
                ) : matchedResumes.length === 0 ? (
                  <div className="text-center py-12">
                    <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Matches Found</h3>
                    <p className="text-gray-500">No resumes match the requirements for this job description.</p>
                  </div>
                ) : (
                  matchedResumes.map((match, index) => (
                    <motion.div
                      key={match.resume_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200 hover:shadow-lg transition-all duration-200"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-3">
                            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                              <span className="text-white font-semibold text-lg">
                                {match.candidate_name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900">
                                {match.candidate_name}
                              </h3>
                              <div className="flex items-center space-x-2">
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                                  match.overall_fit?.includes('Excellent') ? 'bg-green-100 text-green-800' :
                                  match.overall_fit?.includes('Strong') ? 'bg-blue-100 text-blue-800' :
                                  match.overall_fit?.includes('Good') ? 'bg-yellow-100 text-yellow-800' :
                                  match.overall_fit?.includes('Moderate') ? 'bg-orange-100 text-orange-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {match.overall_fit || 'Match'}
                                </span>
                                <span className="text-sm text-gray-500">
                                  Score: {match.score}%
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Enhanced Score Breakdown */}
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div className="bg-white rounded-lg p-3 border border-blue-100">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">
                                  {match.detailed_scores?.skill_match?.toFixed(1) || match.skill_match_percentage?.toFixed(1) || 0}%
                                </div>
                                <div className="text-xs text-gray-600">Skill Match</div>
                              </div>
                            </div>
                            <div className="bg-white rounded-lg p-3 border border-green-100">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">
                                  {match.detailed_scores?.experience_years || 0} years
                                </div>
                                <div className="text-xs text-gray-600">Experience</div>
                              </div>
                            </div>
                            <div className="bg-white rounded-lg p-3 border border-purple-100">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">
                                  {match.score || 0}%
                                </div>
                                <div className="text-xs text-gray-600">Overall Score</div>
                              </div>
                            </div>
                          </div>

                          {/* Match Analysis */}
                          {match.reasons && match.reasons.length > 0 && (
                            <div className="mb-4">
                              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <CheckCircleIcon className="w-4 h-4 mr-2 text-green-500" />
                                Match Analysis
                              </h4>
                              <div className="space-y-2">
                                {match.reasons.slice(0, 3).map((reason, idx) => (
                                  <div key={idx} className="flex items-start space-x-2">
                                    <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                                    <p className="text-sm text-gray-700 leading-relaxed">{reason}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Skills and Missing Skills */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            {match.strengths && match.strengths.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-green-700 mb-2">Strengths</h4>
                                <div className="flex flex-wrap gap-1">
                                  {match.strengths.slice(0, 6).map((skill, idx) => (
                                    <span
                                      key={idx}
                                      className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
                                    >
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {match.missing_skills && match.missing_skills.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-orange-700 mb-2">Missing Skills</h4>
                                <div className="flex flex-wrap gap-1">
                                  {match.missing_skills.slice(0, 6).map((skill, idx) => (
                                    <span
                                      key={idx}
                                      className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium"
                                    >
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Experience Match */}
                          {match.experience_match && (
                            <div className="mb-4">
                              <h4 className="text-sm font-medium text-blue-700 mb-2">Experience Alignment</h4>
                              <div className="bg-blue-50 rounded-lg p-3 border-l-4 border-blue-200">
                                <p className="text-sm text-blue-800 leading-relaxed">
                                  {match.experience_match}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col space-y-2 ml-4">
                          <button
                            onClick={() => handleViewResume(match.resume_id)}
                            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                          >
                            <EyeIcon className="w-4 h-4" />
                            <span>View Resume</span>
                          </button>
                          <button
                            onClick={() => handleDownloadResume(match.resume_id)}
                            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                          >
                            <DocumentArrowDownIcon className="w-4 h-4" />
                            <span>Download</span>
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Resume Detail Modal */}
      {selectedResume && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
          >
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Resume Details</h2>
              <button
                onClick={closeResumeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            <div className="overflow-y-auto max-h-[70vh]">
              <ResumeDetailView
                resume={selectedResume}
                onClose={closeResumeModal}
                onUpdate={() => {}}
              />
            </div>
          </motion.div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && jdToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl max-w-md w-full p-6"
          >
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <TrashIcon className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Delete Job Description
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Are you sure you want to delete "{jdToDelete.title}"? This action cannot be undone.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={cancelDeleteJD}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteJD}
                  className="flex-1 px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default JDManager;
