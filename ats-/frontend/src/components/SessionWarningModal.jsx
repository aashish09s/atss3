import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline';

const SessionWarningModal = ({ isOpen, timeLeft, onExtendSession, onLogout }) => {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black bg-opacity-50"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center space-x-3 mb-4">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-8 w-8 text-amber-500" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Session Timeout Warning
                  </h3>
                  <p className="text-sm text-gray-600">
                    Your session will expire due to inactivity
                  </p>
                </div>
              </div>

              {/* Timer */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-center space-x-2">
                  <ClockIcon className="h-5 w-5 text-amber-600" />
                  <span className="text-2xl font-mono font-bold text-amber-800">
                    {formatTime(timeLeft)}
                  </span>
                </div>
                <p className="text-center text-sm text-amber-700 mt-2">
                  Time remaining before automatic logout
                </p>
              </div>

              {/* Message */}
              <div className="mb-6">
                <p className="text-gray-700 text-sm leading-relaxed">
                  You will be automatically logged out in <strong>{formatTime(timeLeft)}</strong> due to inactivity. 
                  Click "Stay Logged In" to continue your session, or "Logout Now" to end your session immediately.
                </p>
              </div>

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onLogout();
                  }}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                >
                  Logout Now
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onExtendSession();
                  }}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                >
                  Stay Logged In
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default SessionWarningModal;
