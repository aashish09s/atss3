import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PlusIcon,
  DocumentCheckIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  BookmarkIcon,
  FolderOpenIcon,
  TrashIcon,
  PencilIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

const MSA = () => {
  const [activeTab, setActiveTab] = useState('client'); // 'client' or 'candidate'
  const [msaList, setMsaList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Search and Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'signed', 'pending'
  const [dateFilter, setDateFilter] = useState('all'); // 'all', 'today', 'week', 'month'
  const [showFilters, setShowFilters] = useState(false);
  
  // Form state
  const [recipientName, setRecipientName] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [agreementTitle, setAgreementTitle] = useState('');
  const [agreementContent, setAgreementContent] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [companySignerName, setCompanySignerName] = useState('');
  const [companySignerEmail, setCompanySignerEmail] = useState('');
  const [companySignature, setCompanySignature] = useState(null);
  const [companyStamp, setCompanyStamp] = useState(null);
  const [isSending, setIsSending] = useState(false);
  
  // Header customization
  const [companyLogo, setCompanyLogo] = useState(null);
  const [companyAddress, setCompanyAddress] = useState('');
  const [companyGST, setCompanyGST] = useState('');
  const [headerColor, setHeaderColor] = useState('#1F2937');

  // Template management
  const [templates, setTemplates] = useState([]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showSaveTemplateModal, setShowSaveTemplateModal] = useState(false);
  const [templateName, setTemplateName] = useState('');
  
  // Verification method
  const [verificationMethod, setVerificationMethod] = useState('esign'); // 'esign' or 'otp'

  useEffect(() => {
    fetchMSAList();
    fetchTemplates();
  }, [activeTab]);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/api/hr/msa/templates');
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const fetchMSAList = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/hr/msa/?type=${activeTab}`);
      setMsaList(response.data || []);
    } catch (error) {
      console.error('Error fetching MSA list:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMSA = async () => {
    if (!recipientName.trim() || !recipientEmail.trim() || !agreementTitle.trim() || !agreementContent.trim()) {
      alert('Please fill in all required fields');
      return;
    }

    setIsSending(true);
    try {
      const formData = new FormData();
      formData.append('recipient_name', recipientName);
      formData.append('recipient_email', recipientEmail);
      formData.append('agreement_type', activeTab);
      formData.append('agreement_title', agreementTitle);
      formData.append('agreement_content', agreementContent);
      formData.append('company_name', companyName || 'Your Company');
      
      // Only append if not empty (EmailStr validation fails on empty strings)
      if (companySignerName && companySignerName.trim()) {
        formData.append('company_signer_name', companySignerName);
      }
      if (companySignerEmail && companySignerEmail.trim()) {
        formData.append('company_signer_email', companySignerEmail);
      }
      
      if (companySignature) {
        formData.append('company_signature', companySignature);
      }
      if (companyStamp) {
        formData.append('company_stamp', companyStamp);
      }
      
      // Header customization
      if (companyLogo) {
        formData.append('company_logo', companyLogo);
      }
      formData.append('company_address', companyAddress || '');
      formData.append('company_gst', companyGST || '');
      formData.append('header_color', headerColor);
      formData.append('verification_method', verificationMethod); // NEW

      const response = await api.post('/api/hr/msa/initiate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.status === 200) {
        alert('MSA sent successfully with e-signature link!');
        setShowCreateModal(false);
        resetForm();
        fetchMSAList();
      }
    } catch (error) {
      console.error('Error sending MSA:', error);
      const detail = error?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item?.msg || '').join(', ')
        : detail || 'Failed to send MSA. Please try again.';
      alert(message);
    } finally {
      setIsSending(false);
    }
  };

  const resetForm = () => {
    setRecipientName('');
    setRecipientEmail('');
    setAgreementTitle('');
    setAgreementContent('');
    setCompanyName('');
    setCompanySignerName('');
    setCompanySignerEmail('');
    setCompanySignature(null);
    setCompanyStamp(null);
    setCompanyLogo(null);
    setCompanyAddress('');
    setCompanyGST('');
    setHeaderColor('#1F2937');
  };

  const handleSaveAsTemplate = async () => {
    if (!agreementTitle.trim() || !agreementContent.trim()) {
      alert('Please fill in agreement title and content before saving as template');
      return;
    }
    setShowSaveTemplateModal(true);
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      alert('Please enter a template name');
      return;
    }

    try {
      const response = await api.post('/api/hr/msa/templates', {
        template_name: templateName,
        agreement_type: activeTab,
        agreement_title: agreementTitle,
        agreement_content: agreementContent,
      });

      if (response.status === 201) {
        alert('Template saved successfully!');
        setShowSaveTemplateModal(false);
        setTemplateName('');
        fetchTemplates();
      }
    } catch (error) {
      console.error('Error saving template:', error);
      alert('Failed to save template. Please try again.');
    }
  };

  const handleLoadTemplate = (template) => {
    setAgreementTitle(template.agreement_title);
    setAgreementContent(template.agreement_content);
    setActiveTab(template.agreement_type);
    setShowTemplateModal(false);
    alert('Template loaded successfully!');
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await api.delete(`/api/hr/msa/templates/${templateId}`);
      alert('Template deleted successfully!');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      alert('Failed to delete template. Please try again.');
    }
  };

  const downloadSignedMSA = async (msa) => {
    if (!msa.signed_pdf_url) {
      alert('Signed PDF is not available yet');
      return;
    }

    try {
      const filename = msa.signed_pdf_url.split('/').pop() || `signed_msa_${msa.recipient_name}.pdf`;
      const downloadUrl = msa.signed_pdf_url.startsWith('http')
        ? msa.signed_pdf_url
        : `${api.defaults.baseURL}${msa.signed_pdf_url}`;

      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download signed PDF');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      signed: {
        icon: CheckCircleIcon,
        text: 'Signed by Both',
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
      },
      pending: {
        icon: ClockIcon,
        text: 'Pending Signature',
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
      },
      company_signed: {
        icon: DocumentCheckIcon,
        text: 'Company Signed',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
      },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor}`}>
        <Icon className="w-4 h-4 mr-1.5" />
        {config.text}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Filter and Search MSA List
  const getFilteredMSAList = () => {
    let filtered = [...msaList];

    // Search filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (msa) =>
          msa.recipient_name?.toLowerCase().includes(searchLower) ||
          msa.recipient_email?.toLowerCase().includes(searchLower) ||
          msa.agreement_title?.toLowerCase().includes(searchLower) ||
          msa.company_name?.toLowerCase().includes(searchLower)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((msa) => msa.status === statusFilter);
    }

    // Date filter
    if (dateFilter !== 'all') {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
      const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

      filtered = filtered.filter((msa) => {
        const msaDate = new Date(msa.created_at);
        if (dateFilter === 'today') {
          return msaDate >= today;
        } else if (dateFilter === 'week') {
          return msaDate >= weekAgo;
        } else if (dateFilter === 'month') {
          return msaDate >= monthAgo;
        }
        return true;
      });
    }

    return filtered;
  };

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setDateFilter('all');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Master Service Agreement (MSA)</h1>
            <p className="mt-2 text-gray-600">
              Manage agreements with clients and candidates
            </p>
          </div>
          <button
            onClick={() => setShowTemplateModal(true)}
            className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors mr-3"
          >
            <FolderOpenIcon className="w-5 h-5 mr-2" />
            Load Template
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            Create New MSA
          </button>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('client')}
              className={`${
                activeTab === 'client'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
            >
              MSA with Client
            </button>
            <button
              onClick={() => setActiveTab('candidate')}
              className={`${
                activeTab === 'candidate'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
            >
              MSA with Candidate
            </button>
          </nav>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            {/* Search Bar */}
            <div className="flex-1 w-full">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, email, title, or company..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>

            {/* Filter Toggle Button */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
                showFilters
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <FunnelIcon className="w-5 h-5" />
              Filters
              {(statusFilter !== 'all' || dateFilter !== 'all') && (
                <span className="ml-1 px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
                  {[statusFilter !== 'all' ? 1 : 0, dateFilter !== 'all' ? 1 : 0].reduce((a, b) => a + b)}
                </span>
              )}
            </button>

            {/* Clear Filters */}
            {(searchTerm || statusFilter !== 'all' || dateFilter !== 'all') && (
              <button
                onClick={clearFilters}
                className="px-4 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors whitespace-nowrap"
              >
                Clear All
              </button>
            )}
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">All Status</option>
                  <option value="signed">Signed</option>
                  <option value="pending">Pending</option>
                </select>
              </div>

              {/* Date Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
                <select
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">Last 7 Days</option>
                  <option value="month">Last 30 Days</option>
                </select>
              </div>
            </motion.div>
          )}

          {/* Results Count */}
          <div className="mt-3 text-sm text-gray-600">
            Showing <span className="font-semibold">{getFilteredMSAList().length}</span> of <span className="font-semibold">{msaList.length}</span> MSAs
          </div>
        </div>

        {/* MSA List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : getFilteredMSAList().length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <DocumentCheckIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {msaList.length === 0 ? 'No MSAs Yet' : 'No Results Found'}
            </h3>
            <p className="text-gray-600">
              {msaList.length === 0
                ? 'Create a new MSA to get started'
                : 'Try adjusting your search or filters'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {activeTab === 'client' ? 'Client' : 'Candidate'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Agreement Title
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sent Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Signed Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {getFilteredMSAList().map((msa) => (
                    <tr key={msa.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <div className="text-sm font-medium text-gray-900">{msa.recipient_name}</div>
                          <div className="text-sm text-gray-500">{msa.recipient_email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{msa.agreement_title}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{formatDate(msa.created_at)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {msa.status === 'signed' ? formatDate(msa.signed_at) : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(msa.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {msa.status === 'signed' && msa.signed_pdf_url ? (
                          <button
                            onClick={() => downloadSignedMSA(msa)}
                            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
                          >
                            <ArrowDownTrayIcon className="w-4 h-4 mr-1.5" />
                            Download
                          </button>
                        ) : (
                          <span className="text-gray-400 text-sm">Awaiting signature</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Create MSA Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Create New MSA - {activeTab === 'client' ? 'Client' : 'Candidate'}
                </h2>

                <div className="space-y-6">
                  {/* Recipient Information */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {activeTab === 'client' ? 'Client' : 'Candidate'} Name *
                      </label>
                      <input
                        type="text"
                        value={recipientName}
                        onChange={(e) => setRecipientName(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="Enter name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {activeTab === 'client' ? 'Client' : 'Candidate'} Email *
                      </label>
                      <input
                        type="email"
                        value={recipientEmail}
                        onChange={(e) => setRecipientEmail(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder="Enter email"
                      />
                    </div>
                  </div>

                  {/* Agreement Details */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Agreement Title *
                    </label>
                    <input
                      type="text"
                      value={agreementTitle}
                      onChange={(e) => setAgreementTitle(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      placeholder="e.g., Master Service Agreement 2025"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Agreement Content *
                    </label>
                    <textarea
                      value={agreementContent}
                      onChange={(e) => setAgreementContent(e.target.value)}
                      rows={12}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      placeholder="Enter the full agreement content here..."
                    />
                  </div>

                  {/* NEW: Verification Method */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Verification Method</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <button
                        type="button"
                        onClick={() => setVerificationMethod('esign')}
                        className={`p-4 border-2 rounded-lg transition-all ${
                          verificationMethod === 'esign'
                            ? 'border-indigo-600 bg-indigo-50'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-lg font-semibold">E-Signature</span>
                          {verificationMethod === 'esign' && (
                            <CheckCircleIcon className="w-6 h-6 text-indigo-600" />
                          )}
                        </div>
                        <p className="text-sm text-gray-600 text-left">
                          Recipient uploads signature image or draws signature online
                        </p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setVerificationMethod('otp')}
                        className={`p-4 border-2 rounded-lg transition-all ${
                          verificationMethod === 'otp'
                            ? 'border-indigo-600 bg-indigo-50'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-lg font-semibold">OTP Verification</span>
                          {verificationMethod === 'otp' && (
                            <CheckCircleIcon className="w-6 h-6 text-indigo-600" />
                          )}
                        </div>
                        <p className="text-sm text-gray-600 text-left">
                          Recipient receives a 6-digit verification code via email
                        </p>
                      </button>
                    </div>
                  </div>

                  {/* Header Customization */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Header Customization</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Logo
                        </label>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setCompanyLogo(e.target.files[0])}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                        <p className="text-xs text-gray-500 mt-1">Recommended: 200x200px, PNG with transparent background</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Header Background Color
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="color"
                            value={headerColor}
                            onChange={(e) => setHeaderColor(e.target.value)}
                            className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                          />
                          <input
                            type="text"
                            value={headerColor}
                            onChange={(e) => setHeaderColor(e.target.value)}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                            placeholder="#1F2937"
                          />
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Address
                        </label>
                        <textarea
                          value={companyAddress}
                          onChange={(e) => setCompanyAddress(e.target.value)}
                          rows={2}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          placeholder="C/O Address Line 1, City, State - Pincode"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          GST / Corporate ID Number
                        </label>
                        <input
                          type="text"
                          value={companyGST}
                          onChange={(e) => setCompanyGST(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          placeholder="e.g., U62090MP2024PTC071854"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Company Information */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Signatory Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Name
                        </label>
                        <input
                          type="text"
                          value={companyName}
                          onChange={(e) => setCompanyName(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          placeholder="Your Company Name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Signer Name
                        </label>
                        <input
                          type="text"
                          value={companySignerName}
                          onChange={(e) => setCompanySignerName(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          placeholder="Authorized Signatory Name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Signer Email
                        </label>
                        <input
                          type="email"
                          value={companySignerEmail}
                          onChange={(e) => setCompanySignerEmail(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          placeholder="Signatory email"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Signature (Optional)
                        </label>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setCompanySignature(e.target.files[0])}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Stamp (Optional)
                        </label>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setCompanyStamp(e.target.files[0])}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Modal Actions */}
                <div className="mt-6 flex gap-3 justify-end">
                  <button
                    onClick={handleSaveAsTemplate}
                    className="flex items-center gap-2 px-4 py-2 text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                    disabled={isSending}
                  >
                    <BookmarkIcon className="w-5 h-5" />
                    Save as Template
                  </button>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setShowCreateModal(false);
                        resetForm();
                      }}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                      disabled={isSending}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleCreateMSA}
                      disabled={isSending}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSending ? 'Sending...' : 'Send MSA'}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* Save Template Modal */}
        {showSaveTemplateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl shadow-xl max-w-md w-full p-6"
            >
              <h3 className="text-xl font-bold text-gray-900 mb-4">Save as Template</h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template Name
                </label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="e.g., Client Agreement Template"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowSaveTemplateModal(false);
                    setTemplateName('');
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveTemplate}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Save Template
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Load Template Modal */}
        {showTemplateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto"
            >
              <div className="p-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-6">Load MSA Template</h3>
                
                {templates.length === 0 ? (
                  <div className="text-center py-12">
                    <FolderOpenIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No templates saved yet.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {templates
                      .filter((t) => t.agreement_type === activeTab)
                      .map((template) => (
                        <div
                          key={template.id}
                          className="border border-gray-200 rounded-lg p-4 hover:border-indigo-400 transition-colors"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold text-gray-900">{template.template_name}</h4>
                            <button
                              onClick={() => handleDeleteTemplate(template.id)}
                              className="text-red-500 hover:text-red-700 transition-colors"
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </div>
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>Title:</strong> {template.agreement_title}
                          </p>
                          <p className="text-xs text-gray-500 mb-3 line-clamp-2">
                            {template.agreement_content.substring(0, 100)}...
                          </p>
                          <button
                            onClick={() => handleLoadTemplate(template)}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                          >
                            <FolderOpenIcon className="w-4 h-4" />
                            Load Template
                          </button>
                        </div>
                      ))}
                  </div>
                )}

                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setShowTemplateModal(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default MSA;

