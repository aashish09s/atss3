import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  HomeIcon,
  DocumentArrowUpIcon,
  DocumentTextIcon,
  UsersIcon,
  ChartBarIcon,
  InboxIcon,
  DocumentDuplicateIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  BriefcaseIcon,
  UserPlusIcon,
  BuildingOfficeIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ReceiptRefundIcon,
  CheckBadgeIcon,
  DocumentCheckIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../store/auth';
import { useClients } from '../store/clients';

const Sidebar = ({ onClose }) => {
  const { user, logout } = useAuth();
  const { clients, loading } = useClients();
  const [clientsExpanded, setClientsExpanded] = React.useState(false);

  const adminNavItems = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: HomeIcon },
    { name: 'Users', path: '/admin/users', icon: UsersIcon },
    { name: 'Services', path: '/admin/services', icon: BriefcaseIcon },
    { name: 'Jobs', path: '/hr/jobs', icon: BriefcaseIcon },
    { name: 'Upload Resume', path: '/hr/upload', icon: DocumentArrowUpIcon },
    { name: 'Resume List', path: '/hr/resumes', icon: UsersIcon },
    { name: 'JD Manager', path: '/hr/jd-manager', icon: DocumentTextIcon },
    { name: 'Parsed Profiles', path: '/hr/parsed-profiles', icon: ChartBarIcon },
    { name: 'Inbox Link', path: '/hr/inbox-link', icon: InboxIcon },
    { name: 'Offer Letters', path: '/hr/offer-letters', icon: DocumentDuplicateIcon },
    { name: 'Signed Offer Letters', path: '/hr/signed-offer-letters', icon: CheckBadgeIcon },
    { name: 'Client Submit', path: '/hr/client-submit', icon: BuildingOfficeIcon },
    { name: 'Client Dashboard', path: '/hr/clients', icon: ChartBarIcon },
    { name: 'MSA', path: '/hr/msa', icon: DocumentCheckIcon },
    { name: 'Candidate Onboarding', path: '/hr/candidate-onboarding', icon: UserPlusIcon },
    { name: 'Assessment Status', path: '/hr/assessment-status', icon: ClipboardDocumentListIcon },
    { name: 'Invoice', path: '/hr/invoice', icon: ReceiptRefundIcon },
    { name: 'Ledger', path: '/hr/ledger', icon: ReceiptRefundIcon },
    { name: 'Expenses', path: '/hr/expenses', icon: ReceiptRefundIcon },
  ];

  const superadminNavItems = [
    { name: 'Dashboard', path: '/superadmin/dashboard', icon: HomeIcon },
    { name: 'Admins', path: '/superadmin/admins', icon: UsersIcon },
  ];

  const hrNavItems = [
    { name: 'Dashboard', path: '/hr/dashboard', icon: HomeIcon },
    { name: 'Jobs', path: '/hr/jobs', icon: BriefcaseIcon },
    { name: 'Upload Resume', path: '/hr/upload', icon: DocumentArrowUpIcon },
    { name: 'Resume List', path: '/hr/resumes', icon: UsersIcon },
    { name: 'JD Manager', path: '/hr/jd-manager', icon: DocumentTextIcon },
    { name: 'Parsed Profiles', path: '/hr/parsed-profiles', icon: ChartBarIcon },
    { name: 'Inbox Link', path: '/hr/inbox-link', icon: InboxIcon },
    { name: 'Offer Letters', path: '/hr/offer-letters', icon: DocumentDuplicateIcon },
    { name: 'Signed Offer Letters', path: '/hr/signed-offer-letters', icon: CheckBadgeIcon },
    { name: 'Client Submit', path: '/hr/client-submit', icon: BuildingOfficeIcon },
    { name: 'Client Dashboard', path: '/hr/clients', icon: ChartBarIcon },
    { name: 'MSA', path: '/hr/msa', icon: DocumentCheckIcon },
    { name: 'Candidate Onboarding', path: '/hr/candidate-onboarding', icon: UserPlusIcon },
    { name: 'Assessment Status', path: '/hr/assessment-status', icon: ClipboardDocumentListIcon },
  ];

  const managerNavItems = [
    { name: 'Dashboard', path: '/manager/dashboard', icon: HomeIcon },
    { name: 'Shared Resumes', path: '/manager/shared-resumes', icon: BriefcaseIcon },
  ];

  const accountantNavItems = [
    { name: 'Invoice', path: '/hr/invoice', icon: ReceiptRefundIcon },
    { name: 'Ledger', path: '/hr/ledger', icon: ReceiptRefundIcon },
    { name: 'Expenses', path: '/hr/expenses', icon: ReceiptRefundIcon },
    { name: 'MSA', path: '/hr/msa', icon: DocumentCheckIcon },
  ];

  const getNavItems = () => {
    switch (user?.role) {
      case 'superadmin':
        return superadminNavItems;
      case 'admin':
        return adminNavItems;
      case 'hr':
        return hrNavItems;
      case 'manager':
        return managerNavItems;
      case 'accountant':
        return accountantNavItems;
      default:
        return [];
    }
  };

  const navItems = getNavItems();

  return (
    <motion.div
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      className="w-64 bg-white shadow-xl h-screen md:h-full flex flex-col"
    >
      {/* Logo/Brand */}
      <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-white">
        <h1 className="text-2xl font-bold text-gray-900">
          SynHireOne
        </h1>
        {/* Close button (mobile) */}
        {onClose && (
          <button
            aria-label="Close menu"
            className="md:hidden p-2 ml-3 rounded-md hover:bg-gray-100"
            onClick={onClose}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      <div className="px-6 pt-2 text-sm text-gray-500">AI-Powered Hiring</div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 pb-32">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-modern text-white shadow-lg transform scale-105'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="h-5 w-5 mr-3" />
            {item.name}
          </NavLink>
        ))}

        {/* Clients Section - Only for HR and Admin users */}
        {(user?.role === 'hr' || user?.role === 'admin') && (
          <div className="mt-6">
            <button
              onClick={() => setClientsExpanded(!clientsExpanded)}
              className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-all duration-200"
            >
              <div className="flex items-center">
                <BuildingOfficeIcon className="h-5 w-5 mr-3" />
                <span>Clients ({clients.length})</span>
              </div>
              {clientsExpanded ? (
                <ChevronDownIcon className="h-4 w-4" />
              ) : (
                <ChevronRightIcon className="h-4 w-4" />
              )}
            </button>

            {clientsExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="ml-4 mt-2 space-y-1"
              >
                {loading ? (
                  <div className="px-4 py-2 text-xs text-gray-500">
                    Loading clients...
                  </div>
                ) : clients.length === 0 ? (
                  <div className="px-4 py-2 text-xs text-gray-500">
                    No clients yet
                  </div>
                ) : (
                  clients.map((client) => (
                    <NavLink
                      key={client.id}
                      to={`/hr/clients/${client.id}`}
                      className={({ isActive }) =>
                        `flex items-center px-4 py-2 text-xs font-medium rounded-lg transition-all duration-200 ${
                          isActive
                            ? 'bg-blue-100 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                        }`
                      }
                    >
                      <BuildingOfficeIcon className="h-4 w-4 mr-2" />
                      <div className="flex-1 min-w-0">
                        <div className="truncate">{client.name}</div>
                        <div className="truncate text-gray-500">{client.company}</div>
                      </div>
                    </NavLink>
                  ))
                )}
              </motion.div>
            )}
          </div>
        )}
      </nav>

      {/* User Info & Logout */}
      <div className="p-4 border-t border-gray-200 bg-white sticky bottom-0">
        <NavLink
          to="/profile"
          className="flex items-center space-x-3 mb-4 p-2 rounded-lg hover:bg-gray-100 transition-colors"
          onClick={onClose}
        >
          <div className="w-10 h-10 bg-gradient-modern rounded-full flex items-center justify-center">
            <span className="text-white font-semibold text-sm">
              {user?.username?.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.username}
            </p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </NavLink>
        
        <button
          onClick={logout}
          className="w-full flex items-center px-4 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-red-50 hover:text-red-700 transition-colors"
        >
          <ArrowRightOnRectangleIcon className="h-5 w-5 mr-3" />
          Logout
        </button>
      </div>
    </motion.div>
  );
};

export default Sidebar;
