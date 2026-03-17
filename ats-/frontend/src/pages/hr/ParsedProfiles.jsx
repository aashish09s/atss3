import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { UserIcon, EnvelopeIcon, PhoneIcon, TagIcon } from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import EmptyState from '../../components/EmptyState';
import api from '../../utils/api';

const ParsedProfiles = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfile, setSelectedProfile] = useState(null);

  // Helper function to format summary text into readable sections
  const formatSummaryText = (text) => {
    if (!text) return [];
    
    // Ensure text is a string
    const textStr = String(text);
    
    // Clean up the text first
    let cleanText = textStr
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/([.!?])\s*([A-Z])/g, '$1 $2') // Ensure proper spacing after punctuation
      .trim();
    
    // If text is too short, return as is
    if (cleanText.length < 20) {
      return [cleanText];
    }
    
    try {
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
    } catch (error) {
      console.error('Error formatting summary text:', error);
      // Fallback: return the original text as a single section
      return [cleanText];
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    try {
      // Fetch both parsed profiles and resumes for complete data
      const [profilesResponse, resumesResponse] = await Promise.all([
        api.get('/api/hr/parsed/'),
        api.get('/api/hr/resumes')
      ]);
      
      const profiles = profilesResponse.data;
      const resumes = resumesResponse.data;
      
      // Merge data to get complete profile information
      const enhancedProfiles = profiles.map(profile => {
        // Find matching resume
        const resume = resumes.find(r => r.id === profile.resume_id);
        
        if (resume && resume.parsed_data) {
          // Merge data, prioritizing detailed profile data over preview data
          return {
            ...profile,
            // Use full data from parsed profile, fallback to resume data
            skills: profile.skills && profile.skills.length > 0 ? profile.skills : resume.parsed_data.skills || [],
            summary: profile.summary || resume.parsed_data.summary || '',
            // Add any additional data from resume
            resume_filename: resume.filename,
            upload_date: resume.created_at,
            status: resume.status
          };
        }
        
        return profile;
      });
      
      setProfiles(enhancedProfiles);
    } catch (error) {
      console.error('Error fetching profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header title="Parsed Profiles" subtitle="AI-parsed candidate information" />
        <div className="mt-6 flex justify-center">
          <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header 
        title="Parsed Profiles" 
        subtitle="AI-extracted candidate information from resumes"
      />

      <div className="mt-6">
        {profiles.length === 0 ? (
          <EmptyState
            icon={UserIcon}
            title="No Parsed Profiles"
            description="Upload some resumes to see AI-parsed candidate profiles here"
            actionLabel="Upload Resume"
            action={() => window.location.href = '/hr/upload'}
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {profiles.map((profile, index) => (
              <motion.div
                key={profile.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-sm p-6 card-hover cursor-pointer"
                onClick={() => setSelectedProfile(profile)}
              >
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-gradient-modern rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold text-lg">
                      {profile.candidate_name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">
                      {profile.candidate_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Added {new Date(profile.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {profile.email && (
                    <div className="flex items-center space-x-2 text-sm">
                      <EnvelopeIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600 truncate">{profile.email}</span>
                    </div>
                  )}

                  {profile.phone && (
                    <div className="flex items-center space-x-2 text-sm">
                      <PhoneIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">{profile.phone}</span>
                    </div>
                  )}

                  {profile.skills && profile.skills.length > 0 && (
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <TagIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-700">Skills</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {profile.skills.slice(0, 3).map((skill, skillIndex) => (
                          <span
                            key={skillIndex}
                            className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs"
                          >
                            {skill}
                          </span>
                        ))}
                        {profile.skills.length > 3 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{profile.skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {profile.summary && (
                    <div className="mt-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-gray-400">📄</span>
                        <span className="text-sm font-medium text-gray-700">Summary</span>
                      </div>
                      <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-3 border-l-4 border-indigo-200">
                        <p className="text-sm text-gray-600 leading-relaxed line-clamp-3">
                          {profile.summary.length > 150 
                            ? `${profile.summary.substring(0, 150)}...` 
                            : profile.summary
                          }
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100">
                  <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                    View Full Profile →
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Profile Detail Modal */}
      {selectedProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedProfile.candidate_name}
                  </h2>
                  <p className="text-gray-500">Candidate Profile</p>
                </div>
                <button
                  onClick={() => setSelectedProfile(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                                    {/* Contact Information */}
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3">Contact Information</h3>
                      <div className="space-y-2">
                        {selectedProfile.email && (
                          <div className="flex items-center space-x-3">
                            <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                            <span>{selectedProfile.email}</span>
                          </div>
                        )}
                        {selectedProfile.phone && (
                          <div className="flex items-center space-x-3">
                            <PhoneIcon className="h-5 w-5 text-gray-400" />
                            <span>{selectedProfile.phone}</span>
                          </div>
                        )}
                        {selectedProfile.location && (
                          <div className="flex items-center space-x-3">
                            <div className="h-5 w-5 text-gray-400">📍</div>
                            <span>{selectedProfile.location}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Additional Information */}
                    {(selectedProfile.resume_filename || selectedProfile.status) && (
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-3">Resume Information</h3>
                        <div className="space-y-2">
                          {selectedProfile.resume_filename && (
                            <div className="text-sm">
                              <span className="font-medium text-gray-700">File: </span>
                              <span className="text-gray-600">{selectedProfile.resume_filename}</span>
                            </div>
                          )}
                          {selectedProfile.status && (
                            <div className="text-sm">
                              <span className="font-medium text-gray-700">Status: </span>
                              <span className="text-gray-600 capitalize">{selectedProfile.status.replace(/_/g, ' ')}</span>
                            </div>
                          )}
                          {selectedProfile.upload_date && (
                            <div className="text-sm">
                              <span className="font-medium text-gray-700">Uploaded: </span>
                              <span className="text-gray-600">{new Date(selectedProfile.upload_date).toLocaleDateString()}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                {/* Skills */}
                {selectedProfile.skills && selectedProfile.skills.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedProfile.skills.map((skill, index) => {
                        // Ensure skill is always a string
                        const skillText = typeof skill === 'string' ? skill : String(skill || '');
                        return (
                          <span
                            key={index}
                            className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                          >
                            {skillText}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Experience */}
                {selectedProfile.experience && selectedProfile.experience.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Experience</h3>
                    <div className="space-y-3">
                      {selectedProfile.experience.map((exp, index) => {
                        // Handle both string and object formats
                        if (typeof exp === 'string') {
                          return (
                            <div key={index} className="border-l-4 border-blue-500 pl-4">
                              <p className="text-sm text-gray-600">{exp}</p>
                            </div>
                          );
                        }
                        
                        return (
                          <div key={index} className="border-l-4 border-blue-500 pl-4">
                            <h4 className="font-medium">{exp.title || exp.position || 'Position'}</h4>
                            {exp.company && (
                              <p className="text-sm text-gray-600">{exp.company}</p>
                            )}
                            {exp.years_display && (
                              <p className="text-sm font-semibold text-gray-700">{exp.years_display}</p>
                            )}
                            {exp.duration && (
                              <p className="text-sm text-gray-500">{exp.duration}</p>
                            )}
                            {exp.description && (
                              <p className="text-sm text-gray-600 mt-1">{exp.description}</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Education */}
                {selectedProfile.education && selectedProfile.education.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Education</h3>
                    <div className="space-y-2">
                      {selectedProfile.education.map((edu, index) => {
                        // Handle both string and object formats
                        const eduText = typeof edu === 'string' ? edu : (edu.degree || edu.institution || 'Education');
                        const institution = typeof edu === 'object' ? edu.institution : null;
                        const year = typeof edu === 'object' ? edu.year : null;
                        
                        return (
                          <div key={index} className="bg-gray-50 p-3 rounded-lg">
                            <p className="font-medium">{eduText}</p>
                            {institution && institution !== eduText && (
                              <p className="text-sm text-gray-600">{institution}</p>
                            )}
                            {year && (
                              <p className="text-sm text-gray-500">{year}</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                    {/* Summary */}
                    {selectedProfile.summary && (
                      <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-6 border border-emerald-100">
                        <div className="flex items-center mb-4">
                          <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center mr-3">
                            <span className="text-emerald-600 font-semibold text-sm">💼</span>
                          </div>
                          <h3 className="text-lg font-semibold text-gray-900">Professional Summary</h3>
                        </div>
                        <div className="space-y-4">
                          {formatSummaryText(String(selectedProfile.summary || '')).map((section, index) => (
                            <div key={index} className="relative">
                              <div className="absolute left-0 top-2 w-2 h-2 bg-emerald-400 rounded-full"></div>
                              <p className="text-gray-700 leading-relaxed pl-6 text-justify">
                                {section}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Certifications */}
                    {selectedProfile.certifications && selectedProfile.certifications.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-3">Certifications</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedProfile.certifications.map((cert, index) => {
                            // Ensure cert is always a string
                            const certText = typeof cert === 'string' ? cert : String(cert || '');
                            return (
                              <span
                                key={index}
                                className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                              >
                                {certText}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Projects */}
                    {selectedProfile.projects && selectedProfile.projects.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-3">Key Projects</h3>
                        <div className="space-y-3">
                          {selectedProfile.projects.map((project, index) => {
                            // Handle both string and object formats
                            if (typeof project === 'string') {
                              return (
                                <div key={index} className="bg-gray-50 p-3 rounded-lg">
                                  <p className="text-sm text-gray-700">{project}</p>
                                </div>
                              );
                            }
                            
                            // Handle object format with name, tools, description
                            return (
                              <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                                <h4 className="font-medium text-gray-900 mb-2">
                                  {project.name || 'Project'}
                                </h4>
                                
                                {project.tools && project.tools.length > 0 && (
                                  <div className="mb-2">
                                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Tools:</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {project.tools.map((tool, toolIndex) => (
                                        <span
                                          key={toolIndex}
                                          className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs"
                                        >
                                          {tool}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {project.description && (
                                  <p className="text-sm text-gray-600 leading-relaxed">
                                    {project.description}
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default ParsedProfiles;
