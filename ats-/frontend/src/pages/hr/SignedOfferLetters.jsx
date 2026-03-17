import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircleIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

const SignedOfferLetters = () => {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    fetchOffers();
  }, []);

  const fetchOffers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/hr/offer-signatures/');
      setOffers(response.data || []);
    } catch (error) {
      console.error('Error fetching signed offers:', error);
      alert('Failed to load signed offer letters');
    } finally {
      setLoading(false);
    }
  };

  const downloadSignedPDF = async (offer) => {
    if (!offer.signed_pdf_url) {
      alert('Signed PDF is not available yet');
      return;
    }

    try {
      // Extract filename from URL
      const filename = offer.signed_pdf_url.split('/').pop() || `signed_offer_${offer.candidate_name}.pdf`;
      
      // Download using the public uploads URL
      const downloadUrl = offer.signed_pdf_url.startsWith('http') 
        ? offer.signed_pdf_url 
        : `${api.defaults.baseURL}${offer.signed_pdf_url}`;
      
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
        text: 'Signed',
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        iconColor: 'text-green-600',
      },
      pending: {
        icon: ClockIcon,
        text: 'Pending',
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        iconColor: 'text-yellow-600',
      },
      expired: {
        icon: XCircleIcon,
        text: 'Expired',
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        iconColor: 'text-red-600',
      },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor}`}
      >
        <Icon className={`w-4 h-4 mr-1.5 ${config.iconColor}`} />
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

  const filteredOffers = offers.filter((offer) => {
    if (filterStatus === 'all') return true;
    return offer.status === filterStatus;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading signed offer letters...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Signed Offer Letters</h1>
          <p className="mt-2 text-gray-600">
            View and download all signed offer letters
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={() => setFilterStatus('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filterStatus === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({offers.length})
          </button>
          <button
            onClick={() => setFilterStatus('signed')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filterStatus === 'signed'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Signed ({offers.filter((o) => o.status === 'signed').length})
          </button>
          <button
            onClick={() => setFilterStatus('pending')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filterStatus === 'pending'
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Pending ({offers.filter((o) => o.status === 'pending').length})
          </button>
        </div>

        {/* Offer Letters Table */}
        {filteredOffers.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <CheckCircleIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No offer letters found</h3>
            <p className="text-gray-600">
              {filterStatus === 'all'
                ? 'Start by sending an offer letter from the Offer Letters page'
                : `No ${filterStatus} offer letters at the moment`}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
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
                      Company
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
                  {filteredOffers.map((offer) => (
                    <motion.tr
                      key={offer.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.3 }}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <div className="text-sm font-medium text-gray-900">
                            {offer.candidate_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {offer.candidate_email}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {offer.position_title || 'N/A'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {offer.company_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatDate(offer.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {offer.status === 'signed'
                            ? formatDate(offer.signed_at)
                            : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(offer.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {offer.status === 'signed' && offer.signed_pdf_url ? (
                          <button
                            onClick={() => downloadSignedPDF(offer)}
                            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                          >
                            <ArrowDownTrayIcon className="w-4 h-4 mr-1.5" />
                            Download
                          </button>
                        ) : (
                          <span className="text-gray-400 text-sm">
                            {offer.status === 'pending'
                              ? 'Awaiting signature'
                              : 'Not available'}
                          </span>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default SignedOfferLetters;

