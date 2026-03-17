import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  UserIcon,
  EnvelopeIcon,
  PhoneIcon,
  BriefcaseIcon,
  AcademicCapIcon,
  StarIcon,
  DocumentArrowDownIcon,
  ShareIcon,
  PaperAirplaneIcon,
  CheckCircleIcon,
  ClockIcon,
  ChartBarIcon,
  TagIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../store/auth';
import api from '../utils/api';
import { formatLocalDate, formatLocalDateTime } from '../utils/dateUtils';
import ClientEmailForm from './ClientEmailForm';

const ResumeDetailView = ({ resume, onClose, onUpdate }) => {
  const { user } = useAuth();
  const [parsedProfile, setParsedProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [atsScore, setAtsScore] = useState(null);
  const [statusHistory, setStatusHistory] = useState([]);
  const [showClientEmailForm, setShowClientEmailForm] = useState(false);

  // Helper function to format summary text into readable sections
  const formatSummaryText = (text) => {
    if (!text) return [];
    
    // Clean up the text first
    let cleanText = text
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/([.!?])\s*([A-Z])/g, '$1 $2') // Ensure proper spacing after punctuation
      .trim();
    
    // Split by common section indicators and clean up
    const sections = cleanText
      .split(/(?:SUMMARY|PROFESSIONAL EXPERIENCE|EXPERIENCE|SKILLS|EDUCATION|PROJECTS|CERTIFICATIONS)/i)
      .filter(section => section.trim().length > 20);
    
    // If we don't get good sections, try sentence-based splitting
    if (sections.length <= 1) {
      const sentences = cleanText
        .split(/(?<=[.!?])\s+(?=[A-Z])/)
        .filter(sentence => sentence.trim().length > 20);
      
      // Group sentences into logical paragraphs (every 2-3 sentences)
      const paragraphs = [];
      for (let i = 0; i < sentences.length; i += 2) {
        const paragraph = sentences.slice(i, i + 2).join(' ').trim();
        if (paragraph.length > 30) {
          paragraphs.push(paragraph);
        }
      }
      
      return paragraphs.length > 0 ? paragraphs : [cleanText];
    }
    
    return sections.map(section => section.trim()).filter(section => section.length > 20);
  };

  useEffect(() => {
    if (resume?.id) {
      fetchDetailedProfile();
    }
  }, [resume?.id]);

  const fetchDetailedProfile = async () => {
    try {
      // Use the basic parsed data from resume object first
      if (resume.parsed_data) {
        setParsedProfile({
          candidate_name: resume.parsed_data.name || 'Unknown',
          email: resume.parsed_data.email,
          phone: resume.parsed_data.phone,
          skills: resume.parsed_data.skills || [],
          experience: resume.parsed_data.experience || [],
          education: resume.parsed_data.education || [],
          summary: resume.parsed_data.summary || '',
          // Map fields to match component expectations
          contact_info: {
            email: resume.parsed_data.email,
            phone: resume.parsed_data.phone
          },
          technical_skills: resume.parsed_data.skills || [],
          work_experience: resume.parsed_data.experience || [],
          professional_summary: resume.parsed_data.summary || ''
        });
      }
      
      // Try to fetch more detailed profile data if available
      try {
        // Look for parsed profile by resume_id
        const allProfilesResponse = await api.get('/api/hr/parsed/');
        const matchingProfile = allProfilesResponse.data.find(profile => profile.resume_id === resume.id);
        
        if (matchingProfile) {
          setParsedProfile({
            ...matchingProfile,
            contact_info: {
              email: matchingProfile.email,
              phone: matchingProfile.phone
            },
            technical_skills: matchingProfile.skills || [],
            work_experience: matchingProfile.experience || [],
            professional_summary: matchingProfile.summary || ''
          });
        }
      } catch (detailedError) {
        console.log('Could not fetch detailed profile, using basic data:', detailedError);
      }
      
      // If there's an ATS score, get the details
      if (resume.ats_score) {
        setAtsScore({
          overall_score: resume.ats_score,
          strengths: [],
          missing_skills: [],
          improvement_suggestions: []
        });
      }
    } catch (error) {
      console.error('Error fetching profile data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    setActionLoading(true);
    try {
      await api.patch(`/api/hr/resume/status?resume_id=${resume.id}`, {
        status: newStatus
      });
      
      if (onUpdate) {
        onUpdate({ ...resume, status: newStatus });
      }
    } catch (error) {
      console.error('Error updating status:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleShare = async () => {
    setActionLoading(true);
    try {
      await api.post('/api/hr/resume/share', {
        resume_id: resume.id
      });
      
      if (onUpdate) {
        onUpdate({ ...resume, shared_with_manager: true });
      }
    } catch (error) {
      console.error('Error sharing resume:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await api.get(`/api/hr/resume/download/${resume.id}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', resume.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading resume:', error);
    }
  };

  const handleShareWithClient = () => {
    setShowClientEmailForm(true);
  };

  const handleClientEmailSent = () => {
    setShowClientEmailForm(false);
    // Optionally show a success message or update the UI
  };


  const showNotification = (title, message, type) => {
    // Simple notification - you can replace this with your notification system
    alert(`${title}: ${message}`);
  };

  const statusOptions = [
    { value: 'submission', label: 'Submission', color: 'gray' },
    { value: 'shortlisting', label: 'Shortlisted', color: 'yellow' },
    { value: 'interview', label: 'Interview', color: 'blue' },
    { value: 'select', label: 'Selected', color: 'green' },
    { value: 'reject', label: 'Rejected', color: 'red' },
    { value: 'offer_letter', label: 'Offer Letter', color: 'purple' },
    { value: 'onboarding', label: 'Onboarding', color: 'indigo' }
  ];

  const getStatusColor = (status) => {
    const statusConfig = statusOptions.find(s => s.value === status);
    return statusConfig?.color || 'gray';
  };

  if (!resume) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="resume-detail-modal"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="bg-white rounded-xl shadow-xl max-w-5xl w-full max-h-[95vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <UserIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {parsedProfile?.candidate_name || resume.parsed_data?.name || 'Unknown Candidate'}
                </h2>
                <p className="text-sm text-gray-600">{resume.filename}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 min-h-0">
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Basic Info */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">Contact Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {parsedProfile?.contact_info?.email && (
                        <div className="flex items-center space-x-2">
                          <EnvelopeIcon className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-700">{parsedProfile.contact_info.email}</span>
                        </div>
                      )}
                      {parsedProfile?.contact_info?.phone && (
                        <div className="flex items-center space-x-2">
                          <PhoneIcon className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-700">{parsedProfile.contact_info.phone}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Professional Summary */}
                  {parsedProfile?.professional_summary && (
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                      <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                          <span className="text-blue-600 font-semibold text-sm">📋</span>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900">Professional Summary</h3>
                      </div>
                      <div className="space-y-4">
                        {formatSummaryText(parsedProfile.professional_summary || '').map((section, index) => (
                          <div key={`summary-${index}-${section?.slice(0, 10) || 'empty'}`} className="relative">
                            <div className="absolute left-0 top-2 w-2 h-2 bg-blue-400 rounded-full"></div>
                            <p className="text-gray-700 leading-relaxed pl-6 text-justify">
                              {section}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Skills */}
                  {parsedProfile?.technical_skills?.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <TagIcon className="w-5 h-5 mr-2" />
                        Technical Skills
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {(parsedProfile.technical_skills || []).map((skill, index) => (
                          <span
                            key={`skill-${index}-${skill || 'empty'}`}
                            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Work Experience */}
                  {parsedProfile?.work_experience?.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <BriefcaseIcon className="w-5 h-5 mr-2" />
                        Work Experience
                      </h3>
                      <div className="space-y-4">
                        {(parsedProfile.work_experience || []).map((exp, index) => (
                          <div key={`exp-${index}-${exp?.title || 'empty'}-${exp?.company || 'empty'}`} className="border-l-4 border-blue-200 pl-4">
                            <h4 className="font-medium text-gray-900">{exp.title}</h4>
                            {exp.company && (
                              <p className="text-sm text-blue-600">{exp.company}</p>
                            )}
                            {exp.years_display && (
                              <p className="text-sm font-semibold text-gray-700">{exp.years_display}</p>
                            )}
                            <p className="text-sm text-gray-500">{exp.duration}</p>
                            {exp.description && (
                              <p className="text-sm text-gray-700 mt-2">{exp.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Education */}
                  {parsedProfile?.education?.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <AcademicCapIcon className="w-5 h-5 mr-2" />
                        Education
                      </h3>
                      <div className="space-y-3">
                        {(parsedProfile.education || []).map((edu, index) => (
                          <div key={`edu-${index}-${edu?.degree || 'empty'}-${edu?.institution || 'empty'}`} className="border-l-4 border-green-200 pl-4">
                            <h4 className="font-medium text-gray-900">{edu.degree}</h4>
                            <p className="text-sm text-green-600">{edu.institution}</p>
                            <p className="text-sm text-gray-500">{edu.year}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                  {/* Status */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">Status</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Current:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium bg-${getStatusColor(resume.status)}-100 text-${getStatusColor(resume.status)}-800`}>
                          {statusOptions.find(s => s.value === resume.status)?.label}
                        </span>
                      </div>
                      
                      {user?.role === 'hr' && (
                        <div>
                          <label className="block text-sm text-gray-600 mb-2">Update Status:</label>
                          <select
                            value={resume.status}
                            onChange={(e) => handleStatusChange(e.target.value)}
                            disabled={actionLoading}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                          >
                            {statusOptions.map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* ATS Score */}
                  {atsScore && (
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <ChartBarIcon className="w-5 h-5 mr-2" />
                        ATS Score
                      </h3>
                      <div className="text-center mb-4">
                        <div className="text-3xl font-bold text-blue-600">
                          {(atsScore.overall_score ?? atsScore.score ?? 0).toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-600">Overall Match</div>
                      </div>
                      
                      {/* Enhanced Score Breakdown */}
                      {atsScore.detailed_scores && (
                        <div className="mb-4 space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Text Similarity:</span>
                            <span className="text-sm font-medium text-gray-900">
                              {atsScore.detailed_scores.text_similarity?.toFixed(1) || 0}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Skill Match:</span>
                            <span className="text-sm font-medium text-gray-900">
                              {(atsScore.detailed_scores.skill_match ?? atsScore.skill_match_percentage ?? 0).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Experience:</span>
                            <span className="text-sm font-medium text-gray-900">
                              {atsScore.detailed_scores.experience_alignment?.toFixed(1) || 0}%
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {/* Match Reasons */}
                      {atsScore.reasons && atsScore.reasons.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Match Analysis:</h4>
                          <div className="space-y-1">
                            {(atsScore.reasons || []).map((reason, index) => (
                              <div key={`reason-${index}-${reason?.slice(0, 20) || 'empty'}`} className="flex items-start space-x-2">
                                <CheckCircleIcon className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                <p className="text-xs text-gray-600 leading-relaxed">{reason}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Strengths */}
                      {atsScore.strengths && atsScore.strengths.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-green-700 mb-2">Strengths:</h4>
                          <div className="flex flex-wrap gap-1">
                            {(atsScore.strengths || []).slice(0, 5).map((strength, index) => (
                              <span
                                key={`strength-${index}-${strength || 'empty'}`}
                                className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
                              >
                                {strength}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Missing Skills */}
                      {atsScore.missing_skills && atsScore.missing_skills.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-orange-700 mb-2">Missing Skills:</h4>
                          <div className="flex flex-wrap gap-1">
                            {(atsScore.missing_skills || []).slice(0, 5).map((skill, index) => (
                              <span
                                key={`missing-${index}-${skill || 'empty'}`}
                                className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Experience Match Details */}
                      {atsScore.experience_match && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-blue-700 mb-2">Experience Match:</h4>
                          <div className="bg-blue-50 rounded-lg p-3 border-l-4 border-blue-200">
                            <p className="text-xs text-blue-800 leading-relaxed">
                              {atsScore.experience_match}
                            </p>
                          </div>
                        </div>
                      )}
                      
                      {/* Overall Fit */}
                      {atsScore.overall_fit && (
                        <div className="text-center">
                          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            atsScore.overall_fit.includes('Excellent') ? 'bg-green-100 text-green-800' :
                            atsScore.overall_fit.includes('Strong') ? 'bg-blue-100 text-blue-800' :
                            atsScore.overall_fit.includes('Good') ? 'bg-yellow-100 text-yellow-800' :
                            atsScore.overall_fit.includes('Moderate') ? 'bg-orange-100 text-orange-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {atsScore.overall_fit}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Quick Actions */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">Actions</h3>
                    <div className="space-y-2">
                      <button
                        onClick={handleDownload}
                        className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
                      >
                        <DocumentArrowDownIcon className="w-4 h-4" />
                        <span>Download</span>
                      </button>
                      
                      {user?.role === 'hr' && !resume.shared_with_manager && (
                        <button
                          onClick={handleShare}
                          disabled={actionLoading}
                          className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <ShareIcon className="w-4 h-4" />
                          <span>Share with Manager</span>
                        </button>
                      )}
                      
                      {resume.shared_with_manager && (
                        <div className="flex items-center space-x-2 px-3 py-2 bg-green-100 rounded-lg text-sm text-green-700">
                          <CheckCircleIcon className="w-4 h-4" />
                          <span>Shared with Manager</span>
                        </div>
                      )}

                      {user?.role === 'hr' && (
                        <button
                          onClick={handleShareWithClient}
                          className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg text-sm font-medium transition-colors"
                        >
                          <UserGroupIcon className="w-4 h-4" />
                          <span>Share with Client (Email)</span>
                        </button>
                      )}

                    </div>
                  </div>

                  {/* Timeline */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <ClockIcon className="w-5 h-5 mr-2" />
                      Timeline
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-gray-600">
                          Uploaded on {formatLocalDateTime(resume.created_at, { year: 'numeric', month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                      {resume.shared_with_manager && (
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-gray-600">Shared with manager</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>

      {/* Client Email Form Modal */}
      {showClientEmailForm && (
        <ClientEmailForm
          key="client-email-form"
          isOpen={showClientEmailForm}
          onClose={() => setShowClientEmailForm(false)}
          resume={resume}
          onEmailSent={handleClientEmailSent}
          showNotification={showNotification}
        />
      )}

    </AnimatePresence>
  );
};

export default ResumeDetailView;
