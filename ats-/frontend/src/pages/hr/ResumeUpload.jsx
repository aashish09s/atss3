import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { DocumentArrowUpIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { Upload } from 'react-feather';
import Header from '../../components/Header';
import BulkUpload from '../../components/BulkUpload';
import DuplicateDetectionModal from '../../components/DuplicateDetectionModal';
import api from '../../utils/api';

const ResumeUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('single'); // 'single' or 'bulk'
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateData, setDuplicateData] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setUploadStatus(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setUploadStatus(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/api/hr/resumes/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        },
      });

      // Check if duplicates were found
      if (response.data.duplicates_found) {
        setDuplicateData({
          duplicates: response.data.duplicates,
          candidateInfo: {
            name: response.data.candidate_name,
            email: response.data.candidate_email,
            phone: response.data.candidate_phone
          },
          isBulkUpload: false
        });
        setShowDuplicateModal(true);
      } else {
        setUploadStatus({
          type: 'success',
          message: 'Resume uploaded successfully! Processing in background.',
        });
        setFile(null);
      }
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed. Please try again.',
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const removeFile = () => {
    setFile(null);
    setUploadStatus(null);
  };

  const handleRemoveDuplicates = (removedIds) => {
    // After removing duplicates, proceed with upload
    setUploadStatus({
      type: 'success',
      message: 'Duplicate resumes removed. Resume uploaded successfully!',
    });
    setFile(null);
    setShowDuplicateModal(false);
    setDuplicateData(null);
  };

  const handleCloseDuplicateModal = () => {
    setShowDuplicateModal(false);
    setDuplicateData(null);
    setFile(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6">
      <Header 
        title="Upload Resume" 
        subtitle="Upload candidate resumes for AI-powered parsing and analysis"
      />

      <div className="mt-6 max-w-4xl mx-auto">
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
          <button
            onClick={() => setActiveTab('single')}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
              activeTab === 'single'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Single Upload
          </button>
          <button
            onClick={() => setActiveTab('bulk')}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
              activeTab === 'bulk'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Bulk Upload
          </button>
        </div>

        {activeTab === 'single' ? (
          /* Single Upload Area */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm p-8"
          >
          {!file ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-400 transition-colors cursor-pointer"
            >
              <DocumentArrowUpIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Drop your resume here
              </h3>
              <p className="text-gray-600 mb-4">
                or click to browse files
              </p>
              <p className="text-sm text-gray-500 mb-6">
                Supports PDF, DOC, DOCX files up to 10MB
              </p>
              
              <label className="btn-gradient-primary px-6 py-3 rounded-lg font-medium cursor-pointer inline-block">
                <Upload className="inline h-5 w-5 mr-2" />
                Choose File
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>
          ) : (
            <div className="space-y-4">
              {/* File Preview */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <DocumentArrowUpIcon className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={removeFile}
                  className="text-red-500 hover:text-red-700"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Upload Progress */}
              {uploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full btn-gradient-primary py-3 px-4 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload Resume'}
              </button>
            </div>
          )}
          </motion.div>
        ) : (
          /* Bulk Upload Area */
          <BulkUpload onUploadComplete={() => setUploadStatus({ type: 'success', message: 'Bulk upload completed!' })} />
        )}

        {/* Status Message */}
        {uploadStatus && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`mt-4 p-4 rounded-lg flex items-center space-x-3 ${
              uploadStatus.type === 'success' 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {uploadStatus.type === 'success' ? (
              <CheckCircleIcon className="h-6 w-6 text-green-500" />
            ) : (
              <XCircleIcon className="h-6 w-6 text-red-500" />
            )}
            <p>{uploadStatus.message}</p>
          </motion.div>
        )}

        {/* Help Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4"
        >
          <h4 className="font-medium text-blue-900 mb-2">AI Processing Info</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Resumes are automatically parsed using AI</li>
            <li>• Extracts contact info, skills, experience, and education</li>
            <li>• Processing happens in the background</li>
            <li>• View parsed data in the "Parsed Profiles" section</li>
          </ul>
        </motion.div>
      </div>

      {/* Duplicate Detection Modal */}
      {showDuplicateModal && duplicateData && (
        <DuplicateDetectionModal
          isOpen={showDuplicateModal}
          onClose={handleCloseDuplicateModal}
          duplicates={duplicateData.duplicates}
          candidateInfo={duplicateData.candidateInfo}
          onRemoveDuplicates={handleRemoveDuplicates}
          isBulkUpload={duplicateData.isBulkUpload}
        />
      )}
    </div>
  );
};

export default ResumeUpload;
