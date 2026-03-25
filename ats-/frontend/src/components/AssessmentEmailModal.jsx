import React, { useState } from 'react';
import { XMarkIcon, EnvelopeIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import api from '../utils/api';

const AssessmentEmailModal = ({ match, onClose }) => {
  const [email, setEmail] = useState(match.candidate_email || '');
  const [customMessage, setCustomMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [durationHours, setDurationHours] = useState(0);
  const [durationMinutes, setDurationMinutes] = useState(0);

  const handleSend = async () => {
    if (!email) { setError('Please enter candidate email.'); return; }
    setLoading(true);
    setError('');
    try {
      await api.post('/api/hr/assessments/send', {
        resume_id: match.resume_id,
        jd_id: match.jd_id || '',
        candidate_name: match.candidate_name,
        candidate_email: email,
        jd_title: match.jd_title,
        custom_message: customMessage,
        duration_hours: durationHours,
        duration_minutes: durationMinutes,
      });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl flex flex-col" style={{ maxHeight: '90vh' }}>
        {/* HEADER */}
        <div className="flex-shrink-0 border-b border-gray-200">
          <div className="flex items-center justify-between p-6">
            <div className="flex items-center space-x-2">
              <EnvelopeIcon className="w-5 h-5 text-green-600" />
              <h2 className="text-lg font-semibold text-gray-900">Send Assessment Email</h2>
            </div>
            <button onClick={onClose}><XMarkIcon className="h-6 w-6 text-gray-400 hover:text-gray-600" /></button>
          </div>
        </div>

        {/* BODY */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {sent ? (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <EnvelopeIcon className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Assessment Sent! 🎉</h3>
              <p className="text-gray-500">Assessment link emailed to <strong>{email}</strong></p>
              <p className="text-gray-400 text-sm mt-1">Candidate has 7 days to complete it.</p>
              <button onClick={onClose} className="mt-6 px-8 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">Close</button>
            </div>
          ) : (
            <div className="space-y-4">
            {/* Candidate info */}
            <div className="bg-indigo-50 rounded-xl p-4 flex items-center space-x-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                {match.candidate_name?.charAt(0)?.toUpperCase()}
              </div>
              <div>
                <p className="font-semibold text-gray-900">{match.candidate_name}</p>
                <p className="text-sm text-gray-500">{match.jd_title} — Score: {match.score}%</p>
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Candidate Email <span className="text-red-500">*</span></label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="candidate@email.com" />
              {!match.candidate_email && (
                <p className="text-xs text-orange-500 mt-1">⚠ Email not found in resume — enter manually</p>
              )}
            </div>

            {/* Custom message */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Additional Message <span className="text-gray-400 font-normal">(Optional)</span></label>
              <textarea value={customMessage} onChange={e => setCustomMessage(e.target.value)} rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                placeholder="Add any specific instructions or notes for the candidate..." />
            </div>

            {/* Assessment Duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assessment Time Limit
                <span className="text-gray-400 font-normal ml-1">(0 = no time limit)</span>
              </label>
              <div className="flex items-center space-x-3">
                
                {/* Hours */}
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">Hours</label>
                  <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setDurationHours(h => Math.max(0, h - 1))}
                      className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-base"
                    >−</button>
                    <input
                      type="number"
                      min="0"
                      max="168"
                      value={durationHours}
                      onChange={e => setDurationHours(Math.max(0, Math.min(168, parseInt(e.target.value) || 0)))}
                      className="flex-1 text-center text-sm font-semibold py-2 bg-white border-none outline-none w-12"
                    />
                    <button
                      type="button"
                      onClick={() => setDurationHours(h => Math.min(168, h + 1))}
                      className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-base"
                    >+</button>
                  </div>
                </div>

                <div className="text-gray-400 font-bold mt-4">:</div>

                {/* Minutes */}
                <div className="flex-1">
                  <label className="block text-xs text-gray-500 mb-1">Minutes</label>
                  <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setDurationMinutes(m => Math.max(0, m - 5))}
                      className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-base"
                    >−</button>
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={durationMinutes}
                      onChange={e => setDurationMinutes(Math.max(0, Math.min(59, parseInt(e.target.value) || 0)))}
                      className="flex-1 text-center text-sm font-semibold py-2 bg-white border-none outline-none w-12"
                    />
                    <button
                      type="button"
                      onClick={() => setDurationMinutes(m => Math.min(59, m + 5))}
                      className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-base"
                    >+</button>
                  </div>
                </div>
              </div>

              <p className="text-xs text-gray-400 mt-1.5">
                {durationHours === 0 && durationMinutes === 0
                  ? '⏰ No time limit set — candidate can take as long as needed'
                  : `⏰ Timer starts when candidate clicks "Start Assessment" — ${durationHours > 0 ? durationHours + 'h ' : ''}${durationMinutes > 0 ? durationMinutes + 'm' : ''}`
                }
              </p>
            </div>

            {/* Preview note */}
            <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 text-xs text-gray-500">
              📧 A professional email will be sent with assessment link. The link expires in <strong>7 days</strong>.
            </div>

            {error && <p className="text-sm text-red-500 bg-red-50 p-2 rounded-lg">{error}</p>}
            </div>
          )}
        </div>

        {/* FOOTER */}
        <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 bg-white rounded-b-2xl">
          {!sent && (
            <div className="flex space-x-3">
              <button 
                onClick={onClose} 
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium"
              >
                Cancel
              </button>
              <button 
                onClick={handleSend} 
                disabled={loading}
                className="flex-1 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <PaperAirplaneIcon className="w-4 h-4" />
                    <span>Send Assessment</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssessmentEmailModal;
