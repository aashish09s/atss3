# Deployment Guide for ats.trihdiconsulting.com

This guide explains how to deploy the HirePy application to production using Caddy and PM2.

## Prerequisites

1. **Domain Setup**: Ensure `ats.trihdiconsulting.com` DNS A record points to your server IP
2. **Node.js & npm**: Installed and configured
3. **Python 3.10+**: Installed with virtual environment
4. **Caddy**: Installed and configured
5. **PM2**: Will be installed automatically by deployment script

## Deployment Steps

### 1. Configure Environment Variables

#### Backend Configuration

Copy the production environment template and update with your actual values:

```bash
cd C:\recent\hirepy\hirepy\backend
copy .env.production .env
```

Edit `.env` file with your actual:
- MongoDB connection string
- JWT secrets (generate new ones for production)
- SMTP email credentials
- Gemini API key
- Encryption key

**Important**: Generate a new encryption key for production:
```python
import secrets
print(secrets.token_urlsafe(32))
```

#### Frontend Configuration

The frontend will use `.env.production` automatically during build:
- `VITE_API_BASE=https://ats.trihdiconsulting.com/api`

### 2. Install PM2 (if not already installed)

```bash
npm install -g pm2
```

### 3. Build and Deploy

Run the deployment script:

```bash
cd C:\recent\hirepy\hirepy
.\deploy.bat
```

Or manually:

```powershell
.\deploy.ps1
```

This script will:
- Build the frontend for production
- Install/update PM2
- Start backend with PM2
- Setup PM2 to start on system boot
- Reload Caddy configuration

### 4. Start Caddy

If Caddy is not already running as a service, start it:

```bash
cd C:\recent\hirepy
caddy run --config Caddyfile
```

Or use the provided batch file:

```bash
.\START_CADDY.bat
```

To run Caddy as a Windows service, use NSSM (Non-Sucking Service Manager):

```bash
# Download NSSM from https://nssm.cc/download
nssm install Caddy "C:\path\to\caddy.exe" "run --config C:\recent\hirepy\Caddyfile"
nssm start Caddy
```

## SSL Certificate

Caddy will automatically:
- Obtain SSL certificate from Let's Encrypt
- Renew certificates automatically
- Redirect HTTP to HTTPS

No manual certificate configuration needed!

## PM2 Management

### View Status
```bash
pm2 status
```

### View Logs
```bash
pm2 logs hirepy-backend
```

### Restart Application
```bash
pm2 restart hirepy-backend
```

### Stop Application
```bash
pm2 stop hirepy-backend
```

### Monitor
```bash
pm2 monit
```

### Save PM2 Configuration
```bash
pm2 save
```

## File Structure

```
C:\recent\hirepy\
├── Caddyfile                 # Caddy reverse proxy configuration
├── caddy\
│   └── logs\                 # Caddy logs
└── hirepy\
    ├── backend\
    │   ├── .env              # Production environment variables
    │   ├── app\
    │   └── uploads\          # Uploaded files
    ├── frontend\
    │   ├── dist\             # Built frontend files (served by Caddy)
    │   └── .env.production   # Frontend production config
    ├── ecosystem.config.js   # PM2 configuration
    ├── deploy.ps1            # Deployment script
    └── logs\                 # PM2 logs
```

## URLs

- **Frontend**: https://ats.trihdiconsulting.com
- **Backend API**: https://ats.trihdiconsulting.com/api
- **WebSocket**: wss://ats.trihdiconsulting.com/ws
- **Uploads**: https://ats.trihdiconsulting.com/uploads

## Troubleshooting

### Backend not starting
1. Check PM2 logs: `pm2 logs hirepy-backend`
2. Verify `.env` file exists and has correct values
3. Check Python virtual environment is activated
4. Verify MongoDB connection

### Frontend not loading
1. Verify `frontend/dist` directory exists and has files
2. Check Caddy logs: `C:\recent\hirepy\caddy\logs\error.log`
3. Check browser console for errors

### SSL Certificate Issues
1. Ensure domain DNS points to server IP
2. Check firewall allows ports 80 and 443
3. Verify Caddy can write to certificate storage directory
4. Check Caddy logs for certificate errors

### Port Already in Use
1. Check if port 8000 is in use: `netstat -ano | findstr :8000`
2. Stop conflicting services
3. Update PM2 config if you need to change port

## Updating the Application

After making code changes:

```bash
cd C:\recent\hirepy\hirepy

# Pull latest code (if using git)
git pull

# Rebuild and redeploy
.\deploy.bat
```

## Monitoring

### PM2 Monitoring
```bash
pm2 monit
```

### Caddy Logs
```bash
# Access logs
type C:\recent\hirepy\caddy\logs\access.log

# Error logs
type C:\recent\hirepy\caddy\logs\error.log
```

### Application Logs
```bash
# PM2 logs
pm2 logs

# Backend application logs
type C:\recent\hirepy\hirepy\backend\logs\app.log
```

## Security Checklist

- [ ] Use strong JWT secrets
- [ ] Use secure MongoDB connection string
- [ ] Enable firewall (allow only 80, 443)
- [ ] Keep dependencies updated
- [ ] Regular backups of MongoDB
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for sensitive data
- [ ] Enable CORS only for your domain
- [ ] Review security headers in Caddyfile

## Support

For issues, check:
1. PM2 logs: `pm2 logs`
2. Caddy logs: `C:\recent\hirepy\caddy\logs\`
3. Application logs: `C:\recent\hirepy\hirepy\backend\logs\`

