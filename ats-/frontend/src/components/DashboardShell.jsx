import React from 'react';
import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import Sidebar from './Sidebar';
import { useAuth } from '../store/auth';

const DashboardShell = () => {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const { logout } = useAuth();

  return (
    <div className="flex min-h-screen md:h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {/* Mobile sidebar drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative z-10 w-72 max-w-[80%] h-full bg-white shadow-2xl overflow-hidden">
            <Sidebar onClose={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar with hamburger */}
        <div className="md:hidden sticky top-0 z-40 bg-white border-b border-gray-200">
          <div className="px-4 py-3 flex items-center justify-between">
            <button
              aria-label="Open menu"
              className="p-2 rounded-md bg-gray-100 text-gray-700 focus:outline-none focus:ring-2 focus:ring-violet-500"
              onClick={() => setMobileOpen(true)}
            >
              {/* simple hamburger */}
              <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="font-semibold text-gray-900">SynHireOne</span>
            <button
              aria-label="Logout"
              onClick={logout}
              className="p-2 rounded-md bg-red-50 text-red-600 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-400"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        <motion.main
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex-1 overflow-y-auto bg-gray-50"
        >
          <Outlet />
        </motion.main>
      </div>
    </div>
  );
};

export default DashboardShell;
