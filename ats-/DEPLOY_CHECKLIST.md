# Deployment Checklist ✅

Use this checklist to verify everything is ready before deploying.

## ✅ Prerequisites Checklist

- [x] **DNS Configuration**
  - [ ] `ats.trihdiconsulting.com` A record points to server IP
  - [ ] DNS propagation completed (check with: `nslookup ats.trihdiconsulting.com`)
  
- [x] **Firewall**
  - [ ] Port 80 (HTTP) is open
  - [ ] Port 443 (HTTPS) is open
  - [ ] Port 8000 (Backend) is accessible from localhost (not public)

- [x] **Backend Environment**
  - [ ] `.env` file exists in `backend/` directory
  - [ ] `MONGODB_URI` is set
  - [ ] `JWT_SECRET_KEY` is set (strong random value)
  - [ ] `JWT_REFRESH_SECRET_KEY` is set
  - [ ] `ENVIRONMENT=production`
  - [ ] `DEBUG=false`
  - [ ] `SMTP_*` values are set (if using email)
  - [ ] `ENCRYPTION_KEY` is set (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

- [x] **Frontend Environment**
  - [ ] `.env.production` file exists in `frontend/` directory
  - [ ] `VITE_API_BASE=https://ats.trihdiconsulting.com/api`

- [x] **Software Installed**
  - [ ] Python 3.10+ installed
  - [ ] Node.js and npm installed
  - [ ] PM2 installed (will auto-install if missing)
  - [ ] Caddy installed and accessible

## 🚀 Deployment Steps

1. **Build Frontend**
   ```bash
   cd C:\recent\hirepy\hirepy\frontend
   npm install  # Only if node_modules doesn't exist
   npm run build
   ```

2. **Start Backend with PM2**
   ```bash
   cd C:\recent\hirepy\hirepy
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup  # For auto-start on boot
   ```

3. **Start Caddy**
   ```bash
   cd C:\recent\hirepy
   caddy run --config Caddyfile
   ```

Or use the quick deploy script:
```bash
cd C:\recent\hirepy\hirepy
QUICK_DEPLOY.bat
```

## ✅ Post-Deployment Verification

- [ ] **PM2 Status**: `pm2 status` shows `hirepy-backend` as online
- [ ] **Backend Health**: Visit `https://ats.trihdiconsulting.com/api/health` (should return JSON)
- [ ] **Frontend**: Visit `https://ats.trihdiconsulting.com` (should load React app)
- [ ] **SSL Certificate**: Browser shows green padlock (HTTPS)
- [ ] **API Connection**: Frontend can connect to backend (test login)
- [ ] **Uploads**: Can access uploaded files at `/uploads/*`

## 📝 Useful Commands

```bash
# Check PM2 status
pm2 status

# View backend logs
pm2 logs hirepy-backend

# Restart backend
pm2 restart hirepy-backend

# Check if port 8000 is in use
netstat -ano | findstr :8000

# Check DNS
nslookup ats.trihdiconsulting.com

# Test backend directly
curl http://localhost:8000/api/health

# View Caddy logs
type C:\recent\hirepy\caddy\logs\access.log
```

## 🐛 Troubleshooting

**Issue: Backend won't start**
- Check: `pm2 logs hirepy-backend`
- Verify: `.env` file has all required variables
- Test: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

**Issue: SSL certificate not obtained**
- Check: DNS points to correct IP
- Check: Ports 80 and 443 are open
- Check: Caddy logs for errors
- Wait: DNS propagation may take up to 48 hours

**Issue: Frontend shows connection errors**
- Verify: Backend is running (`pm2 status`)
- Check: API URL in frontend `.env.production`
- Test: Visit `https://ats.trihdiconsulting.com/api/health`

**Issue: 502 Bad Gateway**
- Check: Backend is running on port 8000
- Check: Caddy configuration points to correct port
- Verify: No firewall blocking localhost:8000

