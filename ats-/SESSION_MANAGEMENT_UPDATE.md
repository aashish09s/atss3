# Session Management Update

## Overview
Updated the application's session management to implement activity-based auto-logout with a 10-minute inactivity timeout, replacing the previous token-based expiration that was causing premature logouts.

## Changes Made

### 1. Backend Configuration
- **File**: `backend/app/core/config.py`
- **Change**: Extended JWT access token expiration from 30 minutes to 24 hours (1440 minutes)
- **File**: `backend/env.example`
- **Change**: Updated `ACCESS_TOKEN_EXPIRE_MINUTES=1440`

### 2. Frontend Activity Tracking
- **File**: `frontend/src/store/auth.jsx`
- **Added**: Comprehensive activity tracking system with:
  - 10-minute inactivity timeout
  - 2-minute warning before auto-logout
  - Activity detection for: mouse movements, clicks, keyboard input, scrolling, touch events
  - Automatic session extension on user activity
  - Clean timer management and cleanup

### 3. Session Warning Modal
- **File**: `frontend/src/components/SessionWarningModal.jsx`
- **Added**: User-friendly warning modal that:
  - Shows countdown timer (2 minutes)
  - Provides "Stay Logged In" and "Logout Now" options
  - Displays clear messaging about session timeout
  - Uses modern UI with animations

### 4. App Integration
- **File**: `frontend/src/App.jsx`
- **Added**: Integration of session warning modal with auth context

## How It Works

### Activity Detection
The system tracks user activity through these events:
- `mousedown` - Mouse button presses
- `mousemove` - Mouse movements
- `keypress` - Keyboard input
- `scroll` - Page scrolling
- `touchstart` - Touch interactions
- `click` - Click events

### Session Flow
1. **User Activity**: Any detected activity resets the 10-minute timer
2. **8 Minutes**: Warning modal appears with 2-minute countdown
3. **10 Minutes**: Automatic logout if no activity
4. **User Action**: "Stay Logged In" extends session, "Logout Now" ends session immediately

### Timer Management
- **Inactivity Timer**: 10-minute countdown to logout
- **Warning Timer**: 8-minute countdown to show warning
- **Countdown Timer**: 2-minute visual countdown in warning modal
- **Cleanup**: All timers are properly cleared on logout or component unmount

## Benefits

### For Users
- ✅ **No more premature logouts** while actively using the application
- ✅ **Clear warning system** before auto-logout
- ✅ **Flexible session control** with extend/logout options
- ✅ **Longer sessions** (24 hours vs 30 minutes) for convenience

### For Security
- ✅ **Activity-based timeout** ensures security for inactive sessions
- ✅ **10-minute inactivity limit** prevents unauthorized access
- ✅ **Automatic cleanup** of timers and session data
- ✅ **Clear user feedback** about session status

## Testing

### Manual Testing Steps
1. **Login** to the application
2. **Wait 8 minutes** without any activity
3. **Verify** warning modal appears with 2-minute countdown
4. **Test "Stay Logged In"** - session should extend
5. **Test inactivity** - should auto-logout after 10 minutes total
6. **Test activity** - timer should reset on any user interaction

### Expected Behavior
- ✅ Active users never get logged out unexpectedly
- ✅ Inactive users get clear warning before logout
- ✅ Session extends automatically with any user activity
- ✅ Clean logout process with proper cleanup

## Configuration

### Timeout Settings (in `frontend/src/store/auth.jsx`)
```javascript
const INACTIVITY_TIMEOUT = 10 * 60 * 1000; // 10 minutes
const WARNING_TIME = 2 * 60 * 1000; // 2 minutes warning
```

### Token Expiration (in `backend/app/core/config.py`)
```python
access_token_expire_minutes: int = 1440  # 24 hours
```

## Files Modified
- `backend/app/core/config.py`
- `backend/env.example`
- `frontend/src/store/auth.jsx`
- `frontend/src/App.jsx`
- `frontend/src/components/SessionWarningModal.jsx` (new)

## Files Created
- `frontend/src/components/SessionWarningModal.jsx`
- `SESSION_MANAGEMENT_UPDATE.md` (this file)

The session management system is now fully implemented and ready for use!
