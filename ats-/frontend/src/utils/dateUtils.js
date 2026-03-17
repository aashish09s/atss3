/**
 * Date utility functions for consistent timezone handling
 * This ensures all dates are displayed in the user's local timezone
 */

/**
 * Format a date string to show in user's local timezone
 * @param {string} dateString - ISO date string from backend
 * @param {Object} options - Formatting options
 * @returns {string} Formatted date string
 */
export const formatLocalDate = (dateString, options = {}) => {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return 'Invalid Date';
    }
    
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    };
    
    // Use toLocaleString without timeZoneName to avoid showing offset
    return date.toLocaleString('en-US', { ...defaultOptions, ...options });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Error';
  }
};

/**
 * Format a date string to show in user's local timezone with custom format
 * This function ensures proper timezone conversion without showing offsets
 * @param {string} dateString - ISO date string from backend
 * @param {Object} options - Formatting options
 * @returns {string} Formatted date string
 */
export const formatLocalDateTime = (dateString, options = {}) => {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.warn('Invalid date string:', dateString);
      return 'Invalid Date';
    }
    
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    };
    
    // Convert to local time and format
    const localDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
    
    return localDate.toLocaleString('en-US', { ...defaultOptions, ...options });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Error';
  }
};

/**
 * Format date for display without time (just date)
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted date string
 */
export const formatLocalDateOnly = (dateString) => {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Error';
  }
};

/**
 * Format date for display with time only (no date)
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted time string
 */
export const formatLocalTimeOnly = (dateString) => {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  } catch (error) {
    console.error('Error formatting time:', error);
    return 'Error';
  }
};

/**
 * Format relative time (e.g., "2 hours ago", "3 days ago")
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'Never';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    const diffInMs = now - date;
    const diffInSeconds = Math.floor(diffInMs / 1000);
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);
    
    if (diffInDays > 0) {
      return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    } else if (diffInHours > 0) {
      return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    } else if (diffInMinutes > 0) {
      return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds > 0) {
      return `${diffInSeconds} second${diffInSeconds > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return 'Error';
  }
};

/**
 * Get timezone offset information for debugging
 * @returns {Object} Timezone information
 */
export const getTimezoneInfo = () => {
  const now = new Date();
  return {
    localTime: now.toLocaleString(),
    utcTime: now.toUTCString(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    offset: now.getTimezoneOffset(),
    offsetHours: -(now.getTimezoneOffset() / 60)
  };
};

/**
 * Convert UTC date to local date string for debugging
 * @param {string} utcDateString - UTC date string
 * @returns {Object} Date information for debugging
 */
export const debugDateConversion = (utcDateString) => {
  if (!utcDateString) return { error: 'No date provided' };
  
  try {
    const utcDate = new Date(utcDateString);
    const localDate = new Date(utcDateString);
    
    return {
      original: utcDateString,
      utc: utcDate.toISOString(),
      local: localDate.toLocaleString(),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      offset: localDate.getTimezoneOffset(),
      offsetHours: -(localDate.getTimezoneOffset() / 60)
    };
  } catch (error) {
    return { error: error.message };
  }
};
