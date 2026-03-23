import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  ClipboardDocumentListIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

// ─── COUNTDOWN HOOK ───────────────────────────────────────────────────────────
const useCountdown = (initialSeconds, running) => {
  const [timeLeft, setTimeLeft] = useState(initialSeconds);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!running || timeLeft <= 0) return;
    intervalRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) { clearInterval(intervalRef.current); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(intervalRef.current);
  }, [running]);

  const format = (secs) => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    if (h > 0) return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  };

  return { timeLeft, formatted: format(timeLeft) };
};

// ─── RULES PAGE ───────────────────────────────────────────────────────────────
const RulesPage = ({ assessmentData, totalSeconds, onStart }) => {
  const formattedDuration = () => {
    if (!totalSeconds || totalSeconds <= 0) return '7 days';
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    if (h > 0 && m > 0) return `${h} hour${h>1?'s':''} ${m} min`;
    if (h > 0) return `${h} hour${h>1?'s':''}`;
    return `${m} minute${m>1?'s':''}`;
  };
  const [agreed, setAgreed] = React.useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white mb-6 shadow-xl"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-3">
                <ClipboardDocumentListIcon className="w-7 h-7 text-white opacity-80" />
                <h1 className="text-2xl font-bold">Candidate Assessment</h1>
              </div>
              <p className="text-indigo-100">Role: <strong className="text-white">{assessmentData?.jd_title}</strong></p>
              <p className="text-indigo-100 mt-1">Sent by: {assessmentData?.sent_by_name}</p>
            </div>
            {/* Timer display - top right */}
            <div className="text-center ml-4">
              <p className="text-indigo-200 text-xs font-medium uppercase tracking-wider">Time</p>
              <p className="text-3xl font-bold text-white font-mono mt-1">
                {totalSeconds > 86400 
                  ? formattedDuration() 
                  : totalSeconds > 3600 
                    ? `${Math.floor(totalSeconds/3600)}:${String(Math.floor((totalSeconds%3600)/60)).padStart(2,'0')}:00`
                    : `${String(Math.floor(totalSeconds/60)).padStart(2,'0')}:00`
                }
              </p>
            </div>
          </div>
        </motion.div>

        {/* Rules Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-xl mb-6 overflow-hidden"
        >
          {/* Header bar */}
          <div className="bg-slate-600 px-6 py-4 text-center">
            <h2 className="text-white text-lg font-semibold tracking-wide">
              Instructions for Online Examination
            </h2>
          </div>

          <div className="p-8">
            {/* Warning line */}
            <p className="text-red-600 font-semibold text-sm mb-6">
              Please read the instructions carefully before starting the examination.
            </p>

            {/* Numbered instructions */}
            <ol className="space-y-4">
              {[
                'Click on <strong>Start Assessment</strong> button at the bottom of your screen to begin the examination.',
                'The clock has been set at server and countdown timer at the top right side of the screen will display left out time to closure, from where you can monitor the time you have to complete the exam.',
                'All the answered questions will be counted for calculating the final score.',
                'Do not click <strong>End Exam</strong> button before completing the examination. In case you click End Exam button, you will not be permitted to continue.',
              ].map((text, i) => (
                <li key={i} className="flex items-start space-x-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-slate-100 text-slate-700 rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                    {i + 1}
                  </span>
                  <p
                    className="text-gray-700 text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: text }}
                  />
                </li>
              ))}
            </ol>

            {/* Checkbox */}
            <div className="mt-8 flex items-center space-x-3 border-t border-gray-100 pt-6">
              <input
                type="checkbox"
                id="agree"
                checked={agreed}
                onChange={e => setAgreed(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 cursor-pointer"
              />
              <label htmlFor="agree" className="text-sm text-gray-600 cursor-pointer select-none">
                I have read and understood the instructions given above
              </label>
            </div>
          </div>
        </motion.div>

        {/* Start Button */}
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          onClick={onStart}
          disabled={!agreed}
          className={`w-full py-4 rounded-2xl font-bold text-lg shadow-xl transition-all flex items-center justify-center space-x-3 ${
            agreed 
              ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white cursor-pointer' 
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <PlayIcon className="w-6 h-6" />
          <span>Start Assessment</span>
        </motion.button>
        
        <p className="text-center text-xs text-gray-400 mt-4">
          By clicking Start, the timer will begin and cannot be paused.
        </p>
      </div>
    </div>
  );
};

// ─── QUESTIONS PAGE ───────────────────────────────────────────────────────────
const QuestionsPage = ({ assessmentData, totalSeconds, token, candidateName }) => {
  const { timeLeft, formatted } = useCountdown(totalSeconds, true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const [fullName, setFullName] = useState(candidateName || '');
  const [q1, setQ1] = useState('');
  const [q2, setQ2] = useState('');
  const [q3, setQ3] = useState('');
  const [q4, setQ4] = useState('');
  const [q5, setQ5] = useState('');
  const [q6, setQ6] = useState('');
  const [q7, setQ7] = useState('');

  // Auto submit when time runs out
  useEffect(() => {
    if (timeLeft === 0 && !submitted) {
      handleSubmit(true);
    }
  }, [timeLeft]);

  const handleSubmit = async (autoSubmit = false) => {
    if (!autoSubmit) {
      if (!fullName.trim() || !q1 || !q2 || !q3 || !q4 || !q5 || !q6) {
        setError('Please fill in all required fields before submitting.');
        return;
      }
    }
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/api/assessment/${token}/submit`, {
        full_name: fullName || candidateName,
        responses: {
          current_expected_ctc: q1,
          notice_period: q2,
          total_experience: q3,
          relevant_experience: q4,
          why_interested: q5,
          available_for_interview: q6,
          additional_info: q7,
        }
      });
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit. Please try again.');
      setSubmitting(false);
    }
  };

  if (submitted) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center"
      >
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircleIcon className="w-12 h-12 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-3">Assessment Submitted!</h2>
        <p className="text-gray-500 text-lg">Thank you, <strong>{fullName || candidateName}</strong>!</p>
        <p className="text-gray-400 mt-2">Our HR team will review your responses and get back to you soon.</p>
      </motion.div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
      
      {/* Sticky Top Bar with Timer + Submit */}
      <div className="sticky top-0 z-50 shadow-lg bg-gradient-to-r from-indigo-600 to-purple-600">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-white text-xs opacity-80">Assessment</p>
            <p className="text-white font-semibold text-sm">{assessmentData?.jd_title}</p>
          </div>
          <div className="text-center">
            <p className="text-xs font-medium uppercase tracking-wider text-white opacity-70">Time Remaining</p>
            <p className="text-3xl font-bold font-mono text-white">{formatted}</p>
          </div>
          <button
            onClick={() => handleSubmit(false)}
            disabled={submitting}
            className="bg-white text-indigo-700 hover:bg-indigo-50 font-bold px-5 py-2 rounded-xl text-sm transition-all disabled:opacity-50 shadow"
          >
            {submitting ? 'Submitting...' : 'Submit ✓'}
          </button>
        </div>
      </div>

      {/* Questions Form */}
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-5">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {/* Full Name */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name <span className="text-red-500">*</span></label>
          <input type="text" value={fullName} onChange={e => setFullName(e.target.value)}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm" />
        </div>

        {/* Q1 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Current CTC / Expected CTC <span className="text-red-500">*</span></label>
          <input type="text" value={q1} onChange={e => setQ1(e.target.value)}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            placeholder="e.g. Current: 8 LPA / Expected: 12 LPA" />
        </div>

        {/* Q2 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Notice Period <span className="text-red-500">*</span></label>
          <select value={q2} onChange={e => setQ2(e.target.value)}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm bg-white">
            <option value="">Select notice period</option>
            <option>Immediate / Currently serving notice</option>
            <option>15 days</option>
            <option>30 days</option>
            <option>45 days</option>
            <option>60 days</option>
            <option>90 days</option>
          </select>
        </div>

        {/* Q3 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Total Work Experience <span className="text-red-500">*</span></label>
          <input type="text" value={q3} onChange={e => setQ3(e.target.value)}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            placeholder="e.g. 3 years 6 months" />
        </div>

        {/* Q4 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Relevant Experience for <em>{assessmentData?.jd_title}</em> Role <span className="text-red-500">*</span>
          </label>
          <input type="text" value={q4} onChange={e => setQ4(e.target.value)}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            placeholder="e.g. 2 years in relevant field" />
        </div>

        {/* Q5 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Why are you interested in this role? <span className="text-red-500">*</span></label>
          <textarea value={q5} onChange={e => setQ5(e.target.value)} rows={4}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm resize-none"
            placeholder="Share your motivation..." />
        </div>

        {/* Q6 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Available for Interview? <span className="text-red-500">*</span></label>
          <input type="text" value={q6} onChange={e => setQ6(e.target.value)}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            placeholder="e.g. Weekdays after 5 PM" />
        </div>

        {/* Q7 */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Anything else you'd like to share? <span className="text-gray-400 font-normal">(Optional)</span>
          </label>
          <textarea value={q7} onChange={e => setQ7(e.target.value)} rows={3}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm resize-none"
            placeholder="Any other relevant information..." />
        </div>

      </div>
    </div>
  );
};

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
const AssessmentForm = () => {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [assessmentData, setAssessmentData] = useState(null);
  const [totalSeconds, setTotalSeconds] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    fetchAssessment();
  }, [token]);

  const fetchAssessment = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/assessment/${token}`);
      setAssessmentData(response.data);
      setTotalSeconds(response.data.assessment_duration_seconds || response.data.time_remaining_seconds || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'This assessment link is invalid or has expired.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading assessment...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <ExclamationTriangleIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Link Invalid or Expired</h2>
        <p className="text-gray-500">{error}</p>
      </div>
    </div>
  );

  if (!started) return (
    <RulesPage
      assessmentData={assessmentData}
      totalSeconds={totalSeconds}
      onStart={() => setStarted(true)}
    />
  );

  return (
    <QuestionsPage
      assessmentData={assessmentData}
      totalSeconds={totalSeconds}
      token={token}
      candidateName={assessmentData?.candidate_name}
    />
  );
};

export default AssessmentForm;
