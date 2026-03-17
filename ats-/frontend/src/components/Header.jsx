import React from 'react';
import { motion } from 'framer-motion';
import NotificationDropdown from './NotificationDropdown';

const Header = ({ title, subtitle }) => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-white shadow-sm border-b border-gray-200 px-6 py-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <NotificationDropdown />
        </div>
      </div>
    </motion.header>
  );
};

export default Header;
