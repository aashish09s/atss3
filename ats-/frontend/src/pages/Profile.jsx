import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  UserIcon, 
  EnvelopeIcon, 
  PhoneIcon, 
  BuildingOfficeIcon,
  MapPinIcon,
  CameraIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import Header from '../components/Header';
import api from '../utils/api';
import { formatLocalDate, formatLocalDateTime } from '../utils/dateUtils';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    company_name: '',
    address: ''
  });
  const [nameError, setNameError] = useState('');
  const [phoneError, setPhoneError] = useState('');
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/api/profile/');
      setProfile(response.data);
      setFormData({
        full_name: response.data.full_name || '',
        phone: response.data.phone || '',
        company_name: response.data.company_name || '',
        address: response.data.address || ''
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
      setMessage({ type: 'error', text: 'Failed to load profile' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    // Small validation: prevent digits in full name by stripping them
    if (name === 'full_name') {
      if (/\d/.test(value)) {
        setNameError('Numbers are not allowed in full name');
        const cleaned = value.replace(/\d/g, '');
        setFormData({ ...formData, full_name: cleaned });
        return;
      }
      setNameError('');
    }

    // Small validation for phone: allow leading '+' then digits only, max 14 digits
    if (name === 'phone') {
      // remove all characters except digits and +
      let v = value.replace(/[^+\d]/g, '');
      // if + appears not at start, remove it
      if (v.indexOf('+') > 0) v = v.replace(/\+/g, '');
      let hasPlus = v.startsWith('+');
      let digits = hasPlus ? v.slice(1).replace(/\D/g, '') : v.replace(/\D/g, '');
      if (digits.length > 14) {
        digits = digits.slice(0, 12);
        setPhoneError('Phone number can have at most 14 digits');
      } else {
        setPhoneError('');
      }
      const cleaned = hasPlus ? `+${digits}` : digits;
      setFormData({ ...formData, phone: cleaned });
      return;
    }

    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const response = await api.patch('/api/profile/', formData);
      setProfile(response.data);
      setEditing(false);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
    } catch (error) {
      console.error('Error updating profile:', error);
      setMessage({ type: 'error', text: 'Failed to update profile' });
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = async (file, type) => {
    const formData = new FormData();
    formData.append('file', file);

    const endpoint = type === 'picture' ? '/api/profile/upload-profile-picture' : '/api/profile/upload-company-logo';
    const setUploading = type === 'picture' ? setUploadingPicture : setUploadingLogo;

    setUploading(true);
    try {
      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      await fetchProfile(); // Refresh profile data
      setMessage({ type: 'success', text: `${type === 'picture' ? 'Profile picture' : 'Company logo'} updated successfully!` });
    } catch (error) {
      console.error(`Error uploading ${type}:`, error);
      setMessage({ type: 'error', text: `Failed to upload ${type}` });
    } finally {
      setUploading(false);
    }
  };

  const handleProfilePictureChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file, 'picture');
    }
  };

  const handleCompanyLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file, 'logo');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header title="Profile" subtitle="Manage your account information" />
        <div className="mt-6 flex justify-center">
          <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header title="Profile" subtitle="Manage your account information" />

      {/* Message */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mt-4 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </motion.div>
      )}

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Picture Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-xl shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Picture</h3>
          <div className="flex flex-col items-center">
            <div className="relative">
              <div className="w-32 h-32 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
                {profile?.profile_picture_url ? (
                  <img 
                    src={profile.profile_picture_url} 
                    alt="Profile" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <UserIcon className="w-16 h-16 text-gray-400" />
                )}
              </div>
              <label className="absolute bottom-0 right-0 bg-blue-500 text-white p-2 rounded-full cursor-pointer hover:bg-blue-600 transition-colors">
                <CameraIcon className="w-4 h-4" />
                <input 
                  type="file" 
                  accept="image/*" 
                  onChange={handleProfilePictureChange}
                  className="hidden"
                />
              </label>
            </div>
            {uploadingPicture && (
              <p className="mt-2 text-sm text-gray-600">Uploading...</p>
            )}
          </div>
        </motion.div>

        {/* Company Logo Section */}
        {(profile?.role === 'hr' || profile?.role === 'admin') && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Logo</h3>
            <div className="flex flex-col items-center">
              <div className="relative">
                <div className="w-32 h-32 rounded-lg bg-gray-200 flex items-center justify-center overflow-hidden">
                  {profile?.company_logo_url ? (
                    <img 
                      src={profile.company_logo_url} 
                      alt="Company Logo" 
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <BuildingOfficeIcon className="w-16 h-16 text-gray-400" />
                  )}
                </div>
                <label className="absolute bottom-0 right-0 bg-blue-500 text-white p-2 rounded-full cursor-pointer hover:bg-blue-600 transition-colors">
                  <CameraIcon className="w-4 h-4" />
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleCompanyLogoChange}
                    className="hidden"
                  />
                </label>
              </div>
              {uploadingLogo && (
                <p className="mt-2 text-sm text-gray-600">Uploading...</p>
              )}
            </div>
          </motion.div>
        )}

        {/* Profile Information */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className={`bg-white rounded-xl shadow-sm p-6 ${profile?.role === 'manager' ? 'lg:col-span-2' : ''}`}
        >
          <div className="flex justify-between items-start md:items-center md:flex-row flex-col-reverse gap-3 mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Profile Information</h3>
            </div>
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="btn-gradient-primary px-4 py-2 rounded-lg text-sm font-medium self-end md:self-auto"
              >
                Edit Profile
              </button>
            ) : (
              <div className="flex space-x-2 self-end md:self-auto">
                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="flex items-center space-x-1 bg-green-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-green-600 disabled:opacity-50"
                >
                  <CheckIcon className="w-4 h-4" />
                  <span>{saving ? 'Saving...' : 'Save'}</span>
                </button>
                <button
                  onClick={() => {
                    setEditing(false);
                    setFormData({
                      full_name: profile?.full_name || '',
                      phone: profile?.phone || '',
                      company_name: profile?.company_name || '',
                      address: profile?.address || ''
                    });
                  }}
                  className="flex items-center space-x-1 bg-gray-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-gray-600"
                >
                  <XMarkIcon className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              </div>
            )}
          </div>

          <div className="space-y-4">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                  <UserIcon className="w-5 h-5 text-gray-400" />
                  <span className="text-gray-900">{profile?.username}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg overflow-hidden">
                  <EnvelopeIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span className="text-gray-900 truncate min-w-0">{profile?.email}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                {editing ? (
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    pattern="[a-zA-Z\s\-']*"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your full name (letters only)"
                  />
                ) : (
                  <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                    <UserIcon className="w-5 h-5 text-gray-400" />
                    <span className="text-gray-900">{profile?.full_name || 'Not set'}</span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                {editing ? (
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    inputMode="numeric"
                    pattern="[0-9]*"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your phone number (numbers only)"
                  />
                ) : (
                  <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg overflow-hidden">
                    <PhoneIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    <span className="text-gray-900 truncate min-w-0">{profile?.phone || 'Not set'}</span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name
                </label>
                {editing ? (
                  <input
                    type="text"
                    name="company_name"
                    value={formData.company_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter company name"
                  />
                ) : (
                  <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                    <BuildingOfficeIcon className="w-5 h-5 text-gray-400" />
                    <span className="text-gray-900">{profile?.company_name || 'Not set'}</span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    profile?.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                    profile?.role === 'hr' ? 'bg-green-100 text-green-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {profile?.role?.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Address */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Address
              </label>
              {editing ? (
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your address"
                />
              ) : (
                <div className="flex items-start space-x-2 p-3 bg-gray-50 rounded-lg">
                  <MapPinIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                  <span className="text-gray-900">{profile?.address || 'Not set'}</span>
                </div>
              )}
            </div>

            {/* Account Information */}
            <div className="pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Account Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">Created:</span> {formatLocalDateTime(profile?.created_at, { year: 'numeric', month: 'short', day: 'numeric' })}
                </div>
                <div>
                  <span className="font-medium">Last Updated:</span> {formatLocalDateTime(profile?.updated_at, { year: 'numeric', month: 'short', day: 'numeric' })}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Profile;
