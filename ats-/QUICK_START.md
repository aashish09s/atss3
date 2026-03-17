# Quick Start Deployment Guide

## Prerequisites Check

Before deploying, ensure:
- ✅ Domain `ats.trihdiconsulting.com` DNS points to your server IP
- ✅ Python 3.10+ installed
- ✅ Node.js and npm installed
- ✅ MongoDB connection string ready
- ✅ SMTP email credentials ready
- ✅ Caddy installed

## Quick Deployment (3 Steps)

### Step 1: Configure Environment

```bash
cd C:\recent\hirepy\hirepy\backend
copy .env.production .env
```

Edit `.env` and update:
- `MONGODB_URI` - Your MongoDB connection string
- `JWT_SECRET_KEY` - Generate a secure random string
- `JWT_REFRESH_SECRET_KEY` - Generate another secure random string
- `GEMINI_API_KEY` - Your Gemini API key (optional)
- `SMTP_*` - Your email SMTP settings
- `ENCRYPTION_KEY` - Generate using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `ENVIRONMENT=production`
- `DEBUG=false`

### Step 2: Deploy Application

**Option A - Quick Deploy:**
```bash
cd C:\recent\hirepy\hirepy
QUICK_DEPLOY.bat
```

**Option B - Full Deploy:**
```bash
cd C:\recent\hirepy\hirepy
deploy.bat
```

This will:
- ✅ Build frontend
- ✅ Install/configure PM2
- ✅ Start backend with PM2

### Step 3: Start Caddy

Open a new terminal and run:

```bash
cd C:\recent\hirepy
caddy run --config Caddyfile
```

Or use the batch file:
```bash
START_CADDY.bat
```

Caddy will automatically:
- ✅ Obtain SSL certificate from Let's Encrypt
- ✅ Enable HTTPS
- ✅ Configure reverse proxy
- ✅ Serve your application

## Verify Deployment

1. **Check PM2**: `pm2 status` - Should show `hirepy-backend` as online
2. **Check Caddy**: Look for "certificate obtained successfully" in Caddy output
3. **Visit**: https://ats.trihdiconsulting.com

## Common Commands

```bash
# View backend logs
pm2 logs hirepy-backend

# Restart backend
pm2 restart hirepy-backend

# Monitor processes
pm2 monit

# Stop backend
pm2 stop hirepy-backend

# View Caddy logs
type C:\recent\hirepy\caddy\logs\access.log
```

## Troubleshooting

**Backend won't start:**
- Check `.env` file exists and has all required variables
- Check PM2 logs: `pm2 logs`
- Verify MongoDB connection

**SSL certificate not working:**
- Ensure domain DNS points to server IP (may take time to propagate)
- Check firewall allows ports 80 and 443
- Check Caddy logs for errors

**Frontend shows API errors:**
- Verify backend is running: `pm2 status`
- Check backend logs: `pm2 logs`
- Verify API URL is `https://ats.trihdiconsulting.com/api`

## Next Steps

1. Test login functionality
2. Upload a test resume
3. Create a test job description
4. Monitor logs for any errors

For detailed information, see `DEPLOYMENT.md`

