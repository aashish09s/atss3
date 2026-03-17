import React, { useMemo, useState } from 'react';
import { Dialog } from '@headlessui/react';
import { motion } from 'framer-motion';
import {
  XMarkIcon,
  PaperAirplaneIcon,
  EnvelopeIcon,
  ClipboardDocumentIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import api from '../utils/api';
import { useAuth } from '../store/auth';

const ShareResumeModal = ({ resume, onClose, onShared, showNotification }) => {
  const [managerShareLoading, setManagerShareLoading] = useState(false);
  const [clientShareLoading, setClientShareLoading] = useState(false);
  const [clientEmail, setClientEmail] = useState('');
  const [shareMessage, setShareMessage] = useState('');
  const [validationError, setValidationError] = useState('');
  const { user } = useAuth();

  const hrDetails = useMemo(() => {
    const hrName = user?.full_name || user?.username || 'SynHireOne Team';
    const hrEmail = user?.email || '';
    const company = user?.profile?.company_name || 'SynHireOne';
    return { hrName, hrEmail, company };
  }, [user]);

  const candidateDetails = useMemo(() => {
    const parsed = resume?.parsed_data || {};
    const name = parsed.candidate_name || parsed.name || parsed.full_name || resume?.filename || 'Candidate';
    const position = parsed.current_title || parsed.job_title || parsed.position || 'Candidate';
    return { name, position };
  }, [resume]);

  if (!resume) {
    return null;
  }

  const handleShareWithManager = async () => {
    setManagerShareLoading(true);
    try {
      await api.post('/api/hr/resume/share', { resume_id: resume.id });

      showNotification(
        'Success',
        'Resume shared with your manager successfully.',
        'success'
      );

      onShared?.({ managerShared: true });
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to share with manager.';
      showNotification('Error', message, 'error');
    } finally {
      setManagerShareLoading(false);
    }
  };

  const handleShareWithClient = async () => {
    if (!clientEmail) {
      setValidationError('Client email is required.');
      return;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(clientEmail)) {
      setValidationError('Please enter a valid email address.');
      return;
    }

    setValidationError('');
    setClientShareLoading(true);

    try {
      const subject = `Resume Submission - ${candidateDetails.name}`;
      const emailBody = shareMessage?.trim()
        ? shareMessage.trim()
        : `Hi,

Please find the resume of ${candidateDetails.name} for your review.

Regards,
${hrDetails.hrName}`;

      await api.post('/api/hr/resume/share-with-client', {
        resume_id: resume.id,
        to_emails: clientEmail,
        subject,
        email_body: emailBody,
        candidate_name: candidateDetails.name,
        candidate_position: candidateDetails.position,
        company_name: hrDetails.company,
        hr_name: hrDetails.hrName,
        hr_email: hrDetails.hrEmail,
        resume_attachment: true,
      });

      showNotification(
        'Success',
        `Resume shared with ${clientEmail}.`,
        'success'
      );

      onShared?.({ clientShared: 'sent' });
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to share with client.';
      showNotification('Error', message, 'error');
    } finally {
      setClientShareLoading(false);
    }
  };

  const handleCopyProfileLink = async () => {
    try {
      const profileUrl = `${window.location.origin}/resume/${resume.id}`;
      await navigator.clipboard.writeText(profileUrl);
      showNotification('Copied', 'Profile link copied to clipboard.', 'success');
    } catch (error) {
      showNotification('Error', 'Failed to copy link.', 'error');
    }
  };

  return (
    <Dialog open={Boolean(resume)} onClose={onClose} className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center px-4">
        <Dialog.Overlay className="fixed inset-0 bg-black/40" />

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className="relative z-10 w-full max-w-3xl rounded-2xl bg-white shadow-2xl"
        >
          <header className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
            <div>
              <Dialog.Title className="text-lg font-semibold text-gray-900">
                Share Resume
              </Dialog.Title>
              <p className="text-sm text-gray-500">
                Choose how you want to share <span className="font-medium text-gray-700">{resume.filename}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
              aria-label="Close share modal"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </header>

          <div className="grid gap-6 px-6 py-6 md:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <EnvelopeIcon className="h-6 w-6 text-violet-600" />
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">Share with Manager</h3>
                    <p className="text-sm text-gray-500">
                      Send the resume to your reporting manager for review.
                    </p>
                  </div>
                </div>
                {resume.shared_with_manager && (
                  <span className="flex items-center gap-1 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-600">
                    <CheckCircleIcon className="h-4 w-4" />
                    Shared
                  </span>
                )}
              </div>

              <button
                onClick={handleShareWithManager}
                disabled={managerShareLoading}
                className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-violet-500 to-indigo-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {managerShareLoading ? (
                  <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                    ></path>
                  </svg>
                ) : (
                  <>
                    <PaperAirplaneIcon className="h-5 w-5" />
                    Send to Manager
                  </>
                )}
              </button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <ClipboardDocumentIcon className="h-6 w-6 text-emerald-600" />
                <div>
                  <h3 className="text-base font-semibold text-gray-900">Share with Client</h3>
                  <p className="text-sm text-gray-500">
                    Email the resume directly to a client or external contact.
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Client Email
                  </label>
                  <input
                    type="email"
                    value={clientEmail}
                    onChange={(event) => setClientEmail(event.target.value)}
                    placeholder="client@example.com"
                    className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Message (optional)
                  </label>
                  <textarea
                    value={shareMessage}
                    onChange={(event) => setShareMessage(event.target.value)}
                    rows={3}
                    placeholder="Hi, please review the attached resume for your requirement..."
                    className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>

                {validationError && (
                  <p className="text-xs font-medium text-red-500">{validationError}</p>
                )}

                <button
                  onClick={handleShareWithClient}
                  disabled={clientShareLoading}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {clientShareLoading ? (
                    <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      ></path>
                    </svg>
                  ) : (
                    <>
                      <EnvelopeIcon className="h-5 w-5" />
                      Send to Client
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </div>

          <div className="flex flex-col gap-3 border-t border-gray-100 bg-gray-50 px-6 py-5 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-900">Quick Share</p>
              <p className="text-xs text-gray-500">
                Copy a secure link to share manually in chat apps or CRM.
              </p>
            </div>
            <button
              onClick={handleCopyProfileLink}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition hover:bg-gray-100"
            >
              <ClipboardDocumentIcon className="h-5 w-5" />
              Copy Profile Link
            </button>
          </div>
        </motion.div>
      </div>
    </Dialog>
  );
};

export default ShareResumeModal;
