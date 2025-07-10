// frontend/src/components/AccountPage.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext.tsx';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/apiClient.ts';
import {
  AUTH_PROFILE_ENDPOINT,
  AUTH_UPDATE_USERNAME_ENDPOINT,
  AUTH_CHANGE_PASSWORD_ENDPOINT,
  AUTH_DELETE_ACCOUNT_ENDPOINT
} from '../api/endpoints.ts';

interface ProfileData {
  user_id: string;
  username: string;
  english_level: string;
  total_quizzes: number;
  created_at?: string;
  last_login?: string;
}

const AccountPage: React.FC = () => {
  const { logout, updateUser, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Username change state
  const [newUsername, setNewUsername] = useState('');
  const [isUpdatingUsername, setIsUpdatingUsername] = useState(false);
  
  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  
  // Account deletion state
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/signin');
      return;
    }
    fetchProfile();
  }, [isAuthenticated, navigate]);

  const fetchProfile = async () => {
    try {
      const response = await apiClient.get(AUTH_PROFILE_ENDPOINT);
      if (response.data.success) {
        setProfile(response.data.data);
        setNewUsername(response.data.data.username);
      } else {
        setError('Failed to load profile');
      }
    } catch (err: any) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUsername = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsUpdatingUsername(true);

    try {
      const response = await apiClient.put(AUTH_UPDATE_USERNAME_ENDPOINT, {
        new_username: newUsername.trim()
      });
      
      if (response.data.success) {
        setSuccess('Username updated successfully');
        updateUser({ username: newUsername.trim() });
        setProfile(prev => prev ? { ...prev, username: newUsername.trim() } : null);
      } else {
        setError(response.data.error || 'Failed to update username');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update username');
    } finally {
      setIsUpdatingUsername(false);
    }
  };

  const validatePassword = (password: string) => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/(?=.*[a-zA-Z])(?=.*\d)/.test(password)) {
      return 'Password must contain at least one letter and one number';
    }
    return null;
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const passwordError = validatePassword(newPassword);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setError('New passwords do not match');
      return;
    }

    setIsChangingPassword(true);

    try {
      const response = await apiClient.put(AUTH_CHANGE_PASSWORD_ENDPOINT, {
        current_password: currentPassword,
        new_password: newPassword
      });
      
      if (response.data.success) {
        setSuccess('Password changed successfully. You will be signed out.');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmNewPassword('');
        
        // Sign out user after password change
        setTimeout(() => {
          logout();
          navigate('/signin');
        }, 2000);
      } else {
        setError(response.data.error || 'Failed to change password');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    setError('');
    setSuccess('');
    setIsDeletingAccount(true);

    try {
      const response = await apiClient.delete(AUTH_DELETE_ACCOUNT_ENDPOINT, {
        data: { password: deletePassword }
      });
      
      if (response.data.success) {
        setSuccess('Account deleted successfully');
        setTimeout(() => {
          logout();
          navigate('/');
        }, 2000);
      } else {
        setError(response.data.error || 'Failed to delete account');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete account');
    } finally {
      setIsDeletingAccount(false);
      setShowDeleteConfirm(false);
      setDeletePassword('');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg text-red-600">Failed to load profile</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Account Settings</h1>
      
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}
      
      {success && (
        <div className="mb-6 rounded-md bg-green-50 p-4">
          <div className="text-sm text-green-700">{success}</div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-8">
        {/* Profile Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Current Username</label>
              <p className="mt-1 text-sm text-gray-900">{profile.username}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">English Level</label>
              <p className="mt-1 text-sm text-gray-900 capitalize">{profile.english_level}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Total Quizzes</label>
              <p className="mt-1 text-sm text-gray-900">{profile.total_quizzes}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Member Since</label>
              <p className="mt-1 text-sm text-gray-900">
                {profile.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Change Username */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Change Username</h2>
          <form onSubmit={handleUpdateUsername} className="space-y-4">
            <div>
              <label htmlFor="newUsername" className="block text-sm font-medium text-gray-700">
                New Username
              </label>
              <input
                type="text"
                id="newUsername"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter new username"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                3-20 characters, letters, numbers, and underscores only
              </p>
            </div>
            <button
              type="submit"
              disabled={isUpdatingUsername || newUsername.trim() === profile.username}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUpdatingUsername ? 'Updating...' : 'Update Username'}
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Change Password</h2>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700">
                Current Password
              </label>
              <input
                type="password"
                id="currentPassword"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                New Password
              </label>
              <input
                type="password"
                id="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                At least 8 characters with letters and numbers
              </p>
            </div>
            <div>
              <label htmlFor="confirmNewPassword" className="block text-sm font-medium text-gray-700">
                Confirm New Password
              </label>
              <input
                type="password"
                id="confirmNewPassword"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isChangingPassword}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isChangingPassword ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>

        {/* Delete Account */}
        <div className="bg-white shadow rounded-lg p-6 border-red-200 border">
          <h2 className="text-xl font-semibold text-red-600 mb-4">Danger Zone</h2>
          <p className="text-sm text-gray-600 mb-4">
            Once you delete your account, there is no going back. Please be certain.
          </p>
          
          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              Delete Account
            </button>
          ) : (
            <div className="space-y-4">
              <div>
                <label htmlFor="deletePassword" className="block text-sm font-medium text-gray-700">
                  Enter your password to confirm deletion
                </label>
                <input
                  type="password"
                  id="deletePassword"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-red-500 focus:border-red-500"
                  placeholder="Enter your password"
                  required
                />
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleDeleteAccount}
                  disabled={isDeletingAccount || !deletePassword}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDeletingAccount ? 'Deleting...' : 'Yes, Delete My Account'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeletePassword('');
                  }}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AccountPage;
