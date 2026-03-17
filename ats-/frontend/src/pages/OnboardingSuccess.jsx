import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircleIcon } from '@heroicons/react/24/outline';

const OnboardingSuccess = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-8">
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-lg shadow-lg p-8"
        >
          <CheckCircleIcon className="h-20 w-20 text-green-500 mx-auto mb-6" />
          
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Onboarding Completed Successfully!
          </h1>
          
          <p className="text-gray-600 mb-6">
            Thank you for completing your onboarding process. Your information has been submitted and will be reviewed by our HR team.
          </p>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-medium text-blue-800 mb-2">What happens next?</h3>
            <ul className="text-sm text-blue-700 space-y-1 text-left">
              <li>• Your documents will be reviewed by HR</li>
              <li>• You'll receive further instructions via email</li>
              <li>• Our team will contact you if additional information is needed</li>
            </ul>
          </div>
          
          <p className="text-sm text-gray-500">
            You can now close this window. If you have any questions, please contact HR.
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default OnboardingSuccess;
