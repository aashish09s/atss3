import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircleIcon,
  PencilIcon,
  ArrowUpTrayIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

const MSASignature = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [msaData, setMsaData] = useState(null);
  const [fullName, setFullName] = useState('');
  const [signatureMode, setSignatureMode] = useState('upload'); // 'upload' or 'draw'
  const [signatureFile, setSignatureFile] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isSigning, setIsSigning] = useState(false);
  const [signatureDataURL, setSignatureDataURL] = useState(null);
  
  // NEW: OTP verification state
  const [otpCode, setOtpCode] = useState('');
  const [isVerifyingOTP, setIsVerifyingOTP] = useState(false);

  useEffect(() => {
    fetchMSAData();
  }, [token]);

  const fetchMSAData = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/msa/${token}`);
      setMsaData(response.data);
      setFullName(response.data.recipient_name || '');
    } catch (error) {
      console.error('Error fetching MSA:', error);
      setError(error.response?.data?.detail || 'Failed to load MSA. The link may be invalid or expired.');
    } finally {
      setLoading(false);
    }
  };

  // Drawing functions
  const startDrawing = (e) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    ctx.beginPath();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    setIsDrawing(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing) {
      const canvas = canvasRef.current;
      setSignatureDataURL(canvas.toDataURL('image/png'));
    }
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setSignatureDataURL(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSignatureFile(file);
      // Create preview
      const reader = new FileReader();
      reader.onload = (event) => {
        setSignatureDataURL(event.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const dataURLtoFile = (dataurl, filename) => {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  };

  // NEW: Handle OTP verification
  const handleVerifyOTP = async () => {
    if (!otpCode || otpCode.trim().length !== 6) {
      alert('Please enter a valid 6-digit OTP code');
      return;
    }

    setIsVerifyingOTP(true);
    try {
      const formData = new FormData();
      formData.append('otp_code', otpCode.trim());

      const response = await api.post(`/api/msa/${token}/verify-otp`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.status === 200) {
        alert('MSA verified successfully! You will receive a confirmation email shortly.');
        navigate('/msa-success');
      }
    } catch (error) {
      console.error('Error verifying OTP:', error);

      const detail = error?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item?.msg || '').join(', ')
        : detail || 'Failed to verify OTP. Please check your code and try again.';
      alert(message);
    } finally {
      setIsVerifyingOTP(false);
    }
  };

  const handleSubmit = async () => {
    if (!fullName.trim()) {
      alert('Please enter your full name');
      return;
    }

    let signatureToSubmit = signatureFile;

    if (signatureMode === 'draw') {
      if (!signatureDataURL) {
        alert('Please draw your signature');
        return;
      }
      signatureToSubmit = dataURLtoFile(signatureDataURL, 'signature.png');
    } else {
      if (!signatureFile) {
        alert('Please upload your signature');
        return;
      }
    }

    setIsSigning(true);
    try {
      const formData = new FormData();
      formData.append('full_name', fullName);
      formData.append('signature', signatureToSubmit);

      const response = await api.post(`/api/msa/${token}/sign`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.status === 200) {
        alert('MSA signed successfully! You will receive a confirmation email shortly.');
        navigate('/msa-success');
      }
    } catch (error) {
      console.error('Error signing MSA:', error);
      
      // Check if MSA is already signed (409 Conflict)
      if (error?.response?.status === 409) {
        alert('This MSA has already been signed. Redirecting to confirmation page...');
        navigate('/msa-success');
        return;
      }
      
      const detail = error?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item?.msg || '').join(', ')
        : detail || 'Failed to sign MSA. Please try again.';
      alert(message);
    } finally {
      setIsSigning(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading MSA...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-4xl mx-auto"
      >
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-indigo-600 px-6 py-4">
            <h1 className="text-2xl font-bold text-white">Master Service Agreement</h1>
            <p className="text-indigo-100 mt-1">Review and sign the agreement</p>
          </div>

          {/* Agreement Content */}
          <div className="p-6 border-b">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-2">{msaData.agreement_title}</h2>
              <p className="text-sm text-gray-600">
                From: <span className="font-medium">{msaData.company_name}</span>
              </p>
              <p className="text-sm text-gray-600">
                To: <span className="font-medium">{msaData.recipient_name}</span>
              </p>
            </div>

            <div className="prose max-w-none">
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700">
                  {msaData.agreement_content}
                </pre>
              </div>
            </div>
          </div>

          {/* Signature/Verification Section */}
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {msaData.verification_method === 'otp' ? 'Verify with OTP' : 'Your Signature'}
            </h3>

            {/* OTP Verification Mode */}
            {msaData.verification_method === 'otp' ? (
              <div>
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-indigo-800">
                    <CheckCircleIcon className="w-5 h-5 inline mr-2" />
                    A 6-digit verification code has been sent to your email. Please enter it below to verify the agreement.
                  </p>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Verification Code *
                  </label>
                  <input
                    type="text"
                    value={otpCode}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                      setOtpCode(value);
                    }}
                    maxLength={6}
                    className="w-full px-4 py-3 text-center text-2xl font-mono tracking-widest border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="000000"
                  />
                  <p className="text-xs text-gray-500 mt-2">Enter the 6-digit code from your email</p>
                </div>

                <button
                  onClick={handleVerifyOTP}
                  disabled={isVerifyingOTP || otpCode.length !== 6}
                  className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isVerifyingOTP ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Verifying...
                    </>
                  ) : (
                    <>
                      <CheckCircleIcon className="w-5 h-5 mr-2" />
                      Verify & Approve Agreement
                    </>
                  )}
                </button>
              </div>
            ) : (
              // E-Signature Mode
              <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Signature</h3>

            {/* Name Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name *
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter your full name"
              />
            </div>

            {/* Signature Mode Tabs */}
            <div className="mb-4 flex gap-4">
              <button
                onClick={() => setSignatureMode('upload')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                  signatureMode === 'upload'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <ArrowUpTrayIcon className="w-5 h-5 inline mr-2" />
                Upload Signature
              </button>
              <button
                onClick={() => setSignatureMode('draw')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                  signatureMode === 'draw'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <PencilIcon className="w-5 h-5 inline mr-2" />
                Draw Signature
              </button>
            </div>

            {/* Upload Mode */}
            {signatureMode === 'upload' && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Signature Image *
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                {signatureDataURL && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Preview:</p>
                    <img src={signatureDataURL} alt="Signature preview" className="max-h-32 border border-gray-300" />
                  </div>
                )}
              </div>
            )}

            {/* Draw Mode */}
            {signatureMode === 'draw' && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Draw Your Signature *
                </label>
                <div className="border-2 border-gray-300 rounded-lg bg-white">
                  <canvas
                    ref={canvasRef}
                    width={600}
                    height={200}
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    className="w-full cursor-crosshair"
                  />
                </div>
                <button
                  onClick={clearCanvas}
                  className="mt-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Clear Signature
                </button>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                onClick={handleSubmit}
                disabled={isSigning}
                className="flex-1 inline-flex items-center justify-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isSigning ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Signing...
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="w-5 h-5 mr-2" />
                    Sign Agreement
                  </>
                )}
              </button>
            </div>
              </div>
            )}

            <p className="mt-4 text-sm text-gray-500 text-center">
              By signing this agreement, you acknowledge that you have read and agree to the terms and conditions outlined above.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default MSASignature;

