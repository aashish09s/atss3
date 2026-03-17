import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { InboxIcon, PlusIcon, PlayIcon, TrashIcon } from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import api from '../../utils/api';
import { formatLocalDate, formatLocalDateTime, getTimezoneInfo } from '../../utils/dateUtils';

const InboxLink = () => {
  const [inboxes, setInboxes] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [scanningInbox, setScanningInbox] = useState(null);
  const [formData, setFormData] = useState({
    provider: 'gmail',
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    email: '',
    password: '',
    use_ssl: true,
    scan_schedule: 'daily',
  });

  useEffect(() => {
    fetchInboxes();
  }, []);

  const fetchInboxes = async () => {
    try {
      const response = await api.get('/api/hr/inbox/');
      setInboxes(response.data);
    } catch (error) {
      console.error('Error fetching inboxes:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.post('/api/hr/inbox/link_imap', formData);
      setShowForm(false);
      setFormData({
        provider: 'gmail',
        imap_host: 'imap.gmail.com',
        imap_port: 993,
        email: '',
        password: '',
        use_ssl: true,
        scan_schedule: 'daily',
      });
      fetchInboxes();
    } catch (error) {
      console.error('Error linking inbox:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (provider) => {
    const configs = {
      gmail: {
        imap_host: 'imap.gmail.com',
        imap_port: 993,
        use_ssl: true,
      },
      outlook: {
        imap_host: 'outlook.office365.com',
        imap_port: 993,
        use_ssl: true,
      },
      imap: {
        imap_host: '',
        imap_port: 993,
        use_ssl: true,
      },
    };

    setFormData({
      ...formData,
      provider,
      ...configs[provider],
    });
  };

  const triggerScan = async (inboxId) => {
    setScanningInbox(inboxId);
    try {
      const response = await api.post(`/api/hr/inbox/scan_now/${inboxId}`);
      alert('Scan initiated successfully! The scan is running in the background. Resumes will appear in your Resume List once processed.');
      
      // Refresh inboxes after a delay to update last_scanned_at
      setTimeout(() => {
        fetchInboxes();
      }, 2000);
    } catch (error) {
      console.error('Error triggering scan:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to initiate scan. Please check your email credentials and try again.';
      alert(errorMessage);
    } finally {
      setScanningInbox(null);
    }
  };

  const handleDeleteInbox = async (inboxId, email) => {
    const isConfirmed = window.confirm(
      `Are you sure you want to delete the inbox for ${email}?\n\n` +
      `This will:\n` +
      `• Remove the email connection\n` +
      `• Stop automatic scanning\n` +
      `• Delete all scanning history\n\n` +
      `This action cannot be undone.`
    );
    
    if (isConfirmed) {
      try {
        await api.delete(`/api/hr/inbox/${inboxId}`);
        alert('Inbox deleted successfully!');
        fetchInboxes(); // Refresh the list
      } catch (error) {
        console.error('Error deleting inbox:', error);
        alert('Failed to delete inbox');
      }
    }
  };

  return (
    <div className="p-6">
      <Header 
        title="Email Inbox Linking" 
        subtitle="Connect your email to automatically extract resumes from attachments"
      />

      <div className="mt-6 space-y-6">
        {/* Add Inbox Button */}
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Linked Inboxes</h3>
          <button
            onClick={() => setShowForm(true)}
            className="btn-gradient-primary px-4 py-2 rounded-lg font-medium flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Link Inbox</span>
          </button>
        </div>

        {/* Inbox Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white rounded-lg max-w-md w-full"
            >
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Link Email Inbox</h3>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Provider
                    </label>
                    <select
                      value={formData.provider}
                      onChange={(e) => handleProviderChange(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="gmail">Gmail</option>
                      <option value="outlook">Outlook</option>
                      <option value="imap">Custom IMAP</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="your.email@domain.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Password / App Password
                    </label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter password or app password"
                    />
                  </div>

                  {formData.provider === 'imap' && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          IMAP Host
                        </label>
                        <input
                          type="text"
                          value={formData.imap_host}
                          onChange={(e) => setFormData({ ...formData, imap_host: e.target.value })}
                          required
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="imap.example.com"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          IMAP Port
                        </label>
                        <input
                          type="number"
                          value={formData.imap_port}
                          onChange={(e) => setFormData({ ...formData, imap_port: parseInt(e.target.value) })}
                          required
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="993"
                        />
                      </div>
                    </>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Scan Schedule
                    </label>
                    <select
                      value={formData.scan_schedule}
                      onChange={(e) => setFormData({ ...formData, scan_schedule: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setShowForm(false)}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="btn-gradient-primary px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                    >
                      {loading ? 'Linking...' : 'Link Inbox'}
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </div>
        )}

        {/* Linked Inboxes List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {inboxes.map((inbox, index) => (
            <motion.div
              key={inbox.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-xl shadow-sm p-6 card-hover"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <InboxIcon className="h-8 w-8 text-blue-500" />
                  <div>
                    <h4 className="font-semibold text-gray-900">{inbox.email}</h4>
                    <p className="text-sm text-gray-500 capitalize">{inbox.provider}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => triggerScan(inbox.id)}
                    disabled={scanningInbox === inbox.id}
                    className={`p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors ${
                      scanningInbox === inbox.id ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    title={scanningInbox === inbox.id ? 'Scanning...' : 'Trigger immediate scan'}
                  >
                    {scanningInbox === inbox.id ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    ) : (
                      <PlayIcon className="h-5 w-5" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDeleteInbox(inbox.id, inbox.email)}
                    className="p-2 text-red-600 hover:bg-red-50 hover:text-red-700 rounded-lg transition-all duration-200 group"
                    title="Delete inbox"
                  >
                    <TrashIcon className="h-5 w-5 group-hover:scale-110 transition-transform duration-200" />
                  </button>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Schedule:</span>
                  <span className="capitalize font-medium">{inbox.scan_schedule}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Scan:</span>
                  <span className="font-medium">
                    {formatLocalDateTime(inbox.last_scanned_at)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Timezone:</span>
                  <span className="text-xs text-gray-500">
                    {Intl.DateTimeFormat().resolvedOptions().timeZone}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="text-green-600 font-medium">Active</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {inboxes.length === 0 && (
          <div className="text-center py-12">
            <InboxIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Linked Inboxes</h3>
            <p className="text-gray-500 mb-6">Connect your email to automatically scan for resume attachments</p>
            <button
              onClick={() => setShowForm(true)}
              className="btn-gradient-primary px-6 py-3 rounded-lg font-medium"
            >
              Link Your First Inbox
            </button>
          </div>
        )}

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-blue-50 border border-blue-200 rounded-lg p-4"
        >
          <h4 className="font-medium text-blue-900 mb-2">Email Scanning Info</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Automatically extracts PDF, DOC, DOCX attachments from emails</li>
            <li>• Scans unread emails with resume attachments (PDF, DOC, DOCX)</li>
            <li>• <strong>Click the play button (▶) to manually trigger a scan</strong></li>
            <li>• For Gmail, use App Password instead of regular password</li>
            <li>• Resume parsing happens automatically after extraction</li>
            <li>• Resumes will appear in your Resume List after scanning completes</li>
            <li>• All times are displayed in your local timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</li>
          </ul>
        </motion.div>

        {/* Timezone Debug Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gray-50 border border-gray-200 rounded-lg p-4"
        >
          <h4 className="font-medium text-gray-900 mb-2">Timezone Information</h4>
          <div className="text-sm text-gray-700 space-y-1">
            <div><strong>Your Timezone:</strong> {Intl.DateTimeFormat().resolvedOptions().timeZone}</div>
            <div><strong>Current Local Time:</strong> {new Date().toLocaleString()}</div>
            <div><strong>Current UTC Time:</strong> {new Date().toUTCString()}</div>
            <div><strong>Timezone Offset:</strong> {-(new Date().getTimezoneOffset() / 60)} hours from UTC</div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            If you see time differences, this is likely due to timezone conversion. The backend stores times in UTC, 
            but they are displayed in your local timezone for convenience.
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default InboxLink;
