import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  DocumentArrowUpIcon, 
  FolderArrowDownIcon,
  CheckCircleIcon, 
  XCircleIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';
import DuplicateDetectionModal from './DuplicateDetectionModal';
import api from '../utils/api';

const BulkUpload = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState(null);
  const [zipFile, setZipFile] = useState(null);
  const [uploadMode, setUploadMode] = useState('multiple'); // 'multiple' or 'zip'
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateData, setDuplicateData] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setUploadResults(null);
  };

  const handleZipSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.toLowerCase().endsWith('.zip')) {
      setZipFile(selectedFile);
      setUploadResults(null);
    } else {
      alert('Please select a ZIP file');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    
    if (uploadMode === 'zip') {
      const zipFiles = droppedFiles.filter(file => file.name.toLowerCase().endsWith('.zip'));
      if (zipFiles.length > 0) {
        setZipFile(zipFiles[0]);
      }
    } else {
      const resumeFiles = droppedFiles.filter(file => {
        const ext = file.name.toLowerCase();
        return ext.endsWith('.pdf') || ext.endsWith('.doc') || ext.endsWith('.docx');
      });
      setFiles(resumeFiles);
    }
    setUploadResults(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const uploadMultipleFiles = async () => {
    if (files.length === 0) return;
    
    // Prevent double-clicks and multiple simultaneous uploads
    if (uploading) {
      console.log('Upload already in progress, ignoring duplicate request');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await api.post('/api/hr/resumes/bulk-upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minute timeout for large bulk uploads
      });

      // Check if duplicates were found
      if (response.data.has_duplicates && response.data.duplicates_found.length > 0) {
        setDuplicateData({
          duplicates: response.data.duplicates_found,
          candidateInfo: null, // For bulk upload, we'll show all duplicates
          isBulkUpload: true
        });
        setShowDuplicateModal(true);
      }
      
      setUploadResults(response.data);
      setFiles([]);
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error('Bulk upload error:', error);
      setUploadResults({
        message: 'Upload failed',
        successful_uploads: [],
        errors: [{ filename: 'Unknown', error: error.response?.data?.detail || 'Upload failed' }]
      });
    } finally {
      setUploading(false);
    }
  };

  const uploadZipFile = async () => {
    if (!zipFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('zip_file', zipFile);

    try {
      const response = await api.post('/api/hr/resumes/bulk-upload-zip', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResults(response.data);
      setZipFile(null);
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error('ZIP upload error:', error);
      setUploadResults({
        message: 'ZIP upload failed',
        successful_uploads: [],
        errors: [{ filename: zipFile.name, error: error.response?.data?.detail || 'Upload failed' }]
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleRemoveDuplicates = (removedIds) => {
    setShowDuplicateModal(false);
    setDuplicateData(null);
    // Show success message
    setUploadResults(prev => ({
      ...prev,
      message: `${removedIds.length} duplicate resumes removed. Bulk upload completed!`
    }));
  };

  const handleCloseDuplicateModal = () => {
    setShowDuplicateModal(false);
    setDuplicateData(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm p-6"
    >
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Bulk Resume Upload</h3>

      {/* Upload Mode Toggle */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setUploadMode('multiple')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            uploadMode === 'multiple'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Multiple Files
        </button>
        <button
          onClick={() => setUploadMode('zip')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            uploadMode === 'zip'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          ZIP Archive
        </button>
      </div>

      {uploadMode === 'multiple' ? (
        /* Multiple Files Upload */
        <div>
          {files.length === 0 ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
            >
              <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Drop multiple resume files here
              </h4>
              <p className="text-gray-600 mb-4">
                or click to select files
              </p>
              <label className="btn-gradient-primary px-6 py-3 rounded-lg font-medium cursor-pointer inline-block">
                <CloudArrowUpIcon className="inline h-5 w-5 mr-2" />
                Choose Files
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="max-h-60 overflow-y-auto space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <DocumentArrowUpIcon className="h-6 w-6 text-blue-500" />
                      <div>
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setFiles(files.filter((_, i) => i !== index))}
                      className="text-red-500 hover:text-red-700"
                    >
                      <XCircleIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={uploadMultipleFiles}
                  disabled={uploading}
                  className="flex-1 btn-gradient-primary py-3 px-4 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? `Uploading ${files.length} Files...` : `Upload ${files.length} Files`}
                </button>
                <button
                  onClick={() => setFiles([])}
                  className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* ZIP Upload */
        <div>
          {!zipFile ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
            >
              <FolderArrowDownIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Drop ZIP file with resumes here
              </h4>
              <p className="text-gray-600 mb-4">
                ZIP file will be extracted automatically
              </p>
              <label className="btn-gradient-primary px-6 py-3 rounded-lg font-medium cursor-pointer inline-block">
                <FolderArrowDownIcon className="inline h-5 w-5 mr-2" />
                Choose ZIP File
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleZipSelect}
                  className="hidden"
                />
              </label>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <FolderArrowDownIcon className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{zipFile.name}</p>
                    <p className="text-sm text-gray-500">{formatFileSize(zipFile.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => setZipFile(null)}
                  className="text-red-500 hover:text-red-700"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>

              <button
                onClick={uploadZipFile}
                disabled={uploading}
                className="w-full btn-gradient-primary py-3 px-4 rounded-lg font-medium disabled:opacity-50"
              >
                {uploading ? 'Extracting & Uploading...' : 'Upload ZIP File'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Upload Results */}
      {uploadResults && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-6 p-4 rounded-lg border"
        >
          <h4 className="font-medium mb-3">{uploadResults.message}</h4>
          
          {uploadResults.successful_uploads?.length > 0 && (
            <div className="mb-4">
              <h5 className="text-green-700 font-medium mb-2 flex items-center">
                <CheckCircleIcon className="h-5 w-5 mr-2" />
                Successful Uploads ({uploadResults.successful_uploads.length})
              </h5>
              <div className="space-y-1">
                {uploadResults.successful_uploads.map((item, index) => (
                  <p key={index} className="text-sm text-green-600">
                    ✓ {item.filename}
                  </p>
                ))}
              </div>
            </div>
          )}

          {uploadResults.errors?.length > 0 && (
            <div>
              <h5 className="text-red-700 font-medium mb-2 flex items-center">
                <XCircleIcon className="h-5 w-5 mr-2" />
                Failed Uploads ({uploadResults.errors.length})
              </h5>
              <div className="space-y-1">
                {uploadResults.errors.map((item, index) => (
                  <p key={index} className="text-sm text-red-600">
                    ✗ {item.filename}: {item.error}
                  </p>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

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
    </motion.div>
  );
};

export default BulkUpload;
