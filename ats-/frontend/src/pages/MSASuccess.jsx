import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircleIcon } from '@heroicons/react/24/solid';

const MSASuccess = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full bg-white rounded-lg shadow-xl p-8 text-center"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        >
          <CheckCircleIcon className="w-20 h-20 text-green-500 mx-auto mb-6" />
        </motion.div>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Agreement Signed Successfully!
        </h1>
        
        <p className="text-gray-600 mb-6">
          Thank you for signing the Master Service Agreement. You will receive a confirmation email with the signed document shortly.
        </p>
        
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-blue-800">
            <strong>What's next?</strong><br />
            Both parties will receive a copy of the signed agreement via email. Please keep it for your records.
          </p>
        </div>
        
        <p className="mt-6 text-sm text-gray-500">
          You can safely close this window.
        </p>
      </motion.div>
    </div>
  );
};

export default MSASuccess;

