import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ClipboardDocumentListIcon, 
  CheckCircleIcon, 
  ClockIcon, 
  XCircleIcon,
  EyeIcon,
  EnvelopeIcon,
  UserIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import { showNotification } from '../../components/NotificationSystem';
import api from '../../utils/api';

const statusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
  expired: { label: 'Expired', color: 'bg-red-100 text-red-800', icon: XCircleIcon },
};

const AssessmentStatus = () => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssessment, setSelectedAssessment] = useState(null);

  useEffect(() => {
    fetchAssessments();
  }, []);

  const fetchAssessments = async () => {
    try {
      const res = await api.get('/api/hr/assessments/list');
      setAssessments(res.data || []);
    } catch (err) {
      showNotification('Error', 'Failed to load assessments', 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="p-6">
        <Header title="Assessment Status" subtitle="Track all sent assessments and candidate responses" />

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : assessments.length === 0 ? (
          <div className="text-center py-20">
            <ClipboardDocumentListIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-500">No assessments sent yet</h3>
            <p className="text-gray-400 mt-2">Go to JD Manager → Match Resumes → Send Mail to send assessments</p>
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {/* Stats Row */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[
                { label: 'Total Sent', value: assessments.length, color: 'bg-indigo-50 text-indigo-700', icon: EnvelopeIcon },
                { label: 'Completed', value: assessments.filter(a => a.status === 'completed').length, color: 'bg-green-50 text-green-700', icon: CheckCircleIcon },
                { label: 'Pending', value: assessments.filter(a => a.status === 'pending').length, color: 'bg-yellow-50 text-yellow-700', icon: ClockIcon },
              ].map(stat => (
                <div key={stat.label} className={`${stat.color} rounded-xl p-4 flex items-center space-x-3`}>
                  <stat.icon className="w-8 h-8 opacity-70" />
                  <div>
                    <div className="text-2xl font-bold">{stat.value}</div>
                    <div className="text-sm font-medium opacity-80">{stat.label}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Candidate</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Role / JD</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Sent On</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Completed On</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Selection Decision</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {assessments.map((a) => {
                    const cfg = statusConfig[a.status] || statusConfig.pending;
                    return (
                      <motion.tr 
                        key={a.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                              <span className="text-indigo-700 font-bold text-sm">
                                {a.candidate_name?.charAt(0)?.toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="font-medium text-gray-900 text-sm">{a.candidate_name}</div>
                              <div className="text-xs text-gray-400">{a.candidate_email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-700">{a.jd_title}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{formatDate(a.sent_at)}</td>
                        <td className="px-6 py-4 text-sm text-gray-500">{formatDate(a.completed_at)}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.color}`}>
                            <cfg.icon className="w-3.5 h-3.5" />
                            <span>{cfg.label}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {a.status === 'completed' ? (
                            (() => {
                              const score = a.mcq_result?.percentage ?? null;
                              if (score === null) {
                                return <span className="text-gray-400 text-sm">—</span>;
                              }
                              const isShortlisted = score >= 65;
                              return (
                                <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold ${
                                  isShortlisted 
                                    ? 'bg-green-100 text-green-800 border border-green-200' 
                                    : 'bg-red-100 text-red-800 border border-red-200'
                                }`}>
                                  {isShortlisted ? '✅ Shortlisted' : '❌ Not Shortlisted'}
                                </span>
                              );
                            })()
                          ) : (
                            <span className="text-gray-400 text-sm">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {a.status === 'completed' ? (
                            <button
                              onClick={() => setSelectedAssessment(a)}
                              className="flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                            >
                              <EyeIcon className="w-4 h-4" />
                              <span>View Responses</span>
                            </button>
                          ) : (
                            <span className="text-gray-400 text-sm">—</span>
                          )}
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Response Detail Modal */}
      {selectedAssessment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl max-w-xl w-full shadow-2xl max-h-[85vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Assessment Responses</h2>
                <p className="text-sm text-gray-500">{selectedAssessment.candidate_name} — {selectedAssessment.jd_title}</p>
              </div>
              <button onClick={() => setSelectedAssessment(null)} className="text-gray-400 hover:text-gray-600 text-2xl font-bold">×</button>
            </div>
            <div className="p-6 space-y-4">
              {selectedAssessment.candidate_responses?.responses ? (
                Object.entries({
                  'Current / Expected CTC': selectedAssessment.candidate_responses.responses.current_expected_ctc,
                  'Notice Period': selectedAssessment.candidate_responses.responses.notice_period,
                  'Total Experience': selectedAssessment.candidate_responses.responses.total_experience,
                  'Relevant Experience': selectedAssessment.candidate_responses.responses.relevant_experience,
                  'Why Interested': selectedAssessment.candidate_responses.responses.why_interested,
                  'Available for Interview': selectedAssessment.candidate_responses.responses.available_for_interview,
                  'Additional Info': selectedAssessment.candidate_responses.responses.additional_info,
                }).filter(([, v]) => v).map(([label, value]) => (
                  <div key={label} className="bg-gray-50 rounded-xl p-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{label}</p>
                    <p className="text-gray-800 text-sm">{value}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-400 text-center py-8">No responses available</p>
              )}

              {selectedAssessment.mcq_result && (
                <div className={`rounded-xl p-4 mb-2 flex items-center justify-between ${
                  selectedAssessment.mcq_result.percentage >= 65 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Selection Decision</p>
                    <p className={`text-lg font-bold mt-1 ${selectedAssessment.mcq_result.percentage >= 65 ? 'text-green-700' : 'text-red-700'}`}>
                      {selectedAssessment.mcq_result.percentage >= 65 ? '✅ Shortlisted' : '❌ Not Shortlisted'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">MCQ Score</p>
                    <p className={`text-3xl font-bold ${selectedAssessment.mcq_result.percentage >= 65 ? 'text-green-600' : 'text-red-600'}`}>
                      {selectedAssessment.mcq_result.percentage}%
                    </p>
                  </div>
                </div>
              )}

              {/* MCQ Score */}
              {selectedAssessment.mcq_result && (
                <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-100">
                  <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-3">MCQ Assessment Score</p>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700 text-sm">Score</span>
                    <span className={`text-lg font-bold ${
                      selectedAssessment.mcq_result.percentage >= 70 ? 'text-green-600' :
                      selectedAssessment.mcq_result.percentage >= 40 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {selectedAssessment.mcq_result.correct}/{selectedAssessment.mcq_result.total} ({selectedAssessment.mcq_result.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        selectedAssessment.mcq_result.percentage >= 70 ? 'bg-green-500' :
                        selectedAssessment.mcq_result.percentage >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${selectedAssessment.mcq_result.percentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default AssessmentStatus;

