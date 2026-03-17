import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../utils/api';

const OfferSignature = () => {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [offerData, setOfferData] = useState(null);
  const [error, setError] = useState('');
  const [fullName, setFullName] = useState('');
  const [signatureFile, setSignatureFile] = useState(null);
  const [stampFile, setStampFile] = useState(null);
  const [successData, setSuccessData] = useState(null);

  useEffect(() => {
    const fetchOffer = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/api/offer-signatures/${token}`);
        setOfferData(response.data);
      } catch (err) {
        console.error('Failed to load offer signature details:', err);
        const message =
          err?.response?.data?.detail ||
          'This offer letter link is invalid or has expired.';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchOffer();
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!fullName.trim()) {
      setError('Please enter your full name to accept the offer.');
      return;
    }

    if (!signatureFile) {
      setError('Please upload your signature image to continue.');
      return;
    }

    const formData = new FormData();
    formData.append('full_name', fullName.trim());
    formData.append('signature', signatureFile);
    if (stampFile) {
      formData.append('company_stamp', stampFile);
    }

    try {
      setSubmitting(true);
      const response = await api.post(`/api/offer-signatures/${token}/complete`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSuccessData(response.data);
    } catch (err) {
      console.error('Failed to sign offer letter:', err);
      const message =
        err?.response?.data?.detail ||
        'Unable to submit your signature. The link may have expired.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="spinner w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading offer letter...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-lg bg-white shadow-md rounded-2xl p-8 text-center">
            <h1 className="text-xl font-semibold text-gray-900 mb-3">We’re sorry</h1>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
      );
    }

    if (successData) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-lg bg-white shadow-md rounded-2xl p-8 text-center space-y-4">
            <h1 className="text-2xl font-semibold text-green-600">Thank you!</h1>
            <p className="text-gray-700">
              Your signed offer letter has been submitted successfully. A copy has been emailed to you and the HR team.
            </p>
            {successData?.signed_pdf_url && (
              <a
                href={successData.signed_pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                View Signed Offer Letter
              </a>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 py-10 px-4">
        <div className="max-w-5xl mx-auto space-y-10">
          <div className="bg-white shadow-sm rounded-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-6">
              <h1 className="text-2xl font-semibold">Offer Letter Acceptance</h1>
              <p className="mt-2 text-sm text-blue-100">
                {offerData?.company_name} — {offerData?.hr_name} ({offerData?.hr_email})
              </p>
            </div>
            <div className="p-6 border-b border-gray-200">
              <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: offerData?.offer_html || '' }} />
            </div>
          </div>

          <div className="bg-white shadow-sm rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-1">Sign & Accept Offer</h2>
            <p className="text-sm text-gray-500 mb-6">
              Provide your details below. Your signed copy will be emailed to both you and the HR representative.
            </p>

            {error && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name as acknowledgement"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Signature <span className="text-red-500">*</span>
                </label>
                <input
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={(e) => setSignatureFile(e.target.files?.[0] || null)}
                  className="w-full text-sm text-gray-600"
                  required
                />
                <p className="mt-2 text-xs text-gray-500">
                  Accepted formats: PNG, JPG. For best results, use a transparent PNG signature.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Company Stamp (optional)
                </label>
                <input
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={(e) => setStampFile(e.target.files?.[0] || null)}
                  className="w-full text-sm text-gray-600"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full flex justify-center items-center px-4 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? 'Submitting...' : 'Submit Signed Offer'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  };

  return renderContent();
};

export default OfferSignature;


