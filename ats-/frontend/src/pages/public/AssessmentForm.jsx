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
  const [questions, setQuestions] = useState([]);
  const [loadingQ, setLoadingQ] = useState(true);
  const [answers, setAnswers] = useState({});  // {questionId: selectedOption}
  const [currentQ, setCurrentQ] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);

  // This must come AFTER loadingQ is declared above
  const { timeLeft, formatted } = useCountdown(totalSeconds, !loadingQ);

  useEffect(() => {
    fetchQuestions();
  }, []);

  useEffect(() => {
    if (timeLeft === 0 && !submitted && questions.length > 0) {
      handleSubmit(true);
    }
  }, [timeLeft]);

  const fetchQuestions = async () => {
    try {
      setLoadingQ(true);
      const res = await api.get(`/api/assessment/${token}/questions`);
      setQuestions(res.data.questions || []);
    } catch (err) {
      setError('Failed to load questions. Please refresh the page.');
    } finally {
      setLoadingQ(false);
    }
  };

  const handleAnswer = (questionId, option) => {
    setAnswers(prev => ({ ...prev, [String(questionId)]: option }));
  };

  const handleSubmit = async (autoSubmit = false) => {
    setShowSubmitConfirm(false);
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/api/assessment/${token}/submit`, {
        full_name: candidateName,
        responses: { note: autoSubmit ? 'Auto-submitted on time expiry' : 'Manual submit' },
        mcq_answers: answers,
      });
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit. Please try again.');
      setSubmitting(false);
    }
  };

  const answeredCount = Object.keys(answers).length;
  const totalQ = questions.length;

  if (submitted) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 p-4">
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircleIcon className="w-12 h-12 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-3">Assessment Submitted!</h2>
        <p className="text-gray-500 text-lg">Thank you, <strong>{candidateName}</strong>!</p>
        <p className="text-gray-400 mt-2 text-sm">You answered <strong>{answeredCount}</strong> out of <strong>{totalQ}</strong> questions.</p>
        <p className="text-gray-400 mt-1 text-sm">Our HR team will review your responses and get back to you soon.</p>
      </motion.div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Sticky Top Bar */}
      <div className="sticky top-0 z-50 bg-gradient-to-r from-indigo-600 to-purple-600 shadow-lg">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-white text-xs opacity-70">Assessment</p>
            <p className="text-white font-semibold text-sm">{assessmentData?.jd_title}</p>
          </div>
          <div className="text-center">
            <p className="text-white text-xs opacity-70 uppercase tracking-wider">Time Remaining</p>
            <p className="text-3xl font-bold font-mono text-white">{formatted}</p>
          </div>
          <button
            onClick={() => setShowSubmitConfirm(true)}
            disabled={submitting}
            className="bg-white text-indigo-700 hover:bg-indigo-50 font-bold px-5 py-2 rounded-xl text-sm transition-all disabled:opacity-50 shadow"
          >
            {submitting ? 'Submitting...' : 'End Exam ✓'}
          </button>
        </div>
        {/* Progress bar */}
        <div className="h-1 bg-indigo-800">
          <div
            className="h-1 bg-white transition-all duration-300"
            style={{ width: `${totalQ > 0 ? (answeredCount / totalQ) * 100 : 0}%` }}
          />
        </div>
      </div>

      {/* Loading */}
      {loadingQ ? (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-sm mx-auto px-4">
            <div className="w-14 h-14 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-5"></div>
            <h3 className="text-gray-800 font-semibold text-lg mb-2">Generating Your Questions</h3>
            <p className="text-gray-500 text-sm leading-relaxed mb-4">
              AI is preparing {assessmentData?.jd_title} specific questions for you. 
              This may take up to 60 seconds. Please do not close or refresh the page.
            </p>
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3">
              <p className="text-yellow-700 text-xs font-medium">
                ⏳ Timer is paused until questions load
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto px-4 py-6">

          {/* Question Navigator */}
          <div className="bg-white rounded-2xl shadow-sm p-4 mb-6">
            <p className="text-xs text-gray-500 font-medium mb-3">
              Questions: {answeredCount}/{totalQ} answered
            </p>
            <div className="flex flex-wrap gap-2">
              {questions.map((q, idx) => (
                <button
                  key={q.id}
                  onClick={() => setCurrentQ(idx)}
                  className={`w-9 h-9 rounded-lg text-xs font-bold transition-all ${
                    currentQ === idx
                      ? 'bg-indigo-600 text-white ring-2 ring-indigo-300'
                      : answers[String(q.id)]
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
            <div className="flex items-center space-x-4 mt-3 text-xs text-gray-400">
              <span className="flex items-center space-x-1"><span className="w-3 h-3 rounded bg-green-500 inline-block"></span><span>Answered</span></span>
              <span className="flex items-center space-x-1"><span className="w-3 h-3 rounded bg-gray-200 inline-block"></span><span>Not Answered</span></span>
              <span className="flex items-center space-x-1"><span className="w-3 h-3 rounded bg-indigo-600 inline-block"></span><span>Current</span></span>
            </div>
          </div>

          {/* Current Question */}
          {questions[currentQ] && (
            <motion.div
              key={currentQ}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-2xl shadow-sm p-6 mb-6"
            >
              <div className="flex items-start justify-between mb-4">
                <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                  Question {currentQ + 1} of {totalQ}
                </span>
                {questions[currentQ].topic && (
                  <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
                    {questions[currentQ].topic}
                  </span>
                )}
              </div>
              <p className="text-gray-900 font-medium text-base leading-relaxed mb-6">
                {questions[currentQ].question}
              </p>
              <div className="space-y-3">
                {Object.entries(questions[currentQ].options || {}).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => handleAnswer(questions[currentQ].id, key)}
                    className={`w-full text-left px-5 py-4 rounded-xl border-2 transition-all text-sm font-medium ${
                      answers[String(questions[currentQ].id)] === key
                        ? 'border-indigo-600 bg-indigo-50 text-indigo-900'
                        : 'border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 text-gray-700'
                    }`}
                  >
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold mr-3 ${
                      answers[String(questions[currentQ].id)] === key
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}>{key}</span>
                    {value}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Navigation buttons */}
          <div className="flex justify-between">
            <button
              onClick={() => setCurrentQ(q => Math.max(0, q - 1))}
              disabled={currentQ === 0}
              className="px-6 py-3 border-2 border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-all"
            >
              ← Previous
            </button>
            {currentQ < totalQ - 1 ? (
              <button
                onClick={() => setCurrentQ(q => Math.min(totalQ - 1, q + 1))}
                className="px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-all"
              >
                Next →
              </button>
            ) : (
              <button
                onClick={() => setShowSubmitConfirm(true)}
                className="px-6 py-3 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 transition-all"
              >
                Finish & Submit ✓
              </button>
            )}
          </div>

          {error && <p className="text-red-500 text-sm mt-4 text-center">{error}</p>}
        </div>
      )}

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-yellow-600" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Submit Assessment?</h3>
            <p className="text-gray-500 text-sm mb-2">You have answered <strong>{answeredCount}</strong> out of <strong>{totalQ}</strong> questions.</p>
            {answeredCount < totalQ && (
              <p className="text-orange-500 text-xs mb-4">{totalQ - answeredCount} question(s) unanswered. You cannot change answers after submitting.</p>
            )}
            <div className="flex space-x-3 mt-6">
              <button onClick={() => setShowSubmitConfirm(false)}
                className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50">
                Go Back
              </button>
              <button onClick={() => handleSubmit(false)} disabled={submitting}
                className="flex-1 px-4 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
                {submitting ? 'Submitting...' : 'Yes, Submit'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
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
