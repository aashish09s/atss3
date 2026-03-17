# 🚀 Production Deployment - Quick Reference

## ✅ Pre-Deployment Checklist (COMPLETED)

- ✅ DNS: `ats.trihdiconsulting.com` → Your Server IP
- ✅ Firewall: Ports 80 & 443 open
- ✅ Backend `.env`: Production values configured
- ✅ Frontend `.env.production`: Created and configured
- ✅ PM2: Installed
- ✅ Caddy: Installed

## 🎯 Deploy in 2 Commands

### 1. Deploy Application
```bash
cd C:\recent\hirepy\hirepy
START_DEPLOYMENT.bat
```

### 2. Start Caddy (New Terminal)
```bash
cd C:\recent\hirepy
START_CADDY.bat
```

**That's it!** Your application will be live at:
- **Frontend**: https://ats.trihdiconsulting.com
- **Backend API**: https://ats.trihdiconsulting.com/api

## 🔍 Verify Deployment

Run verification script:
```bash
VERIFY_DEPLOYMENT.bat
```

Or manually check:
```bash
# Check PM2
pm2 status

# Check backend health
curl https://ats.trihdiconsulting.com/api/health

# View logs
pm2 logs
```

## 📝 Configuration Files

### Backend: `backend/.env`
```env
ENVIRONMENT=production
DEBUG=false
BACKEND_BASE_URL=https://ats.trihdiconsulting.com
FRONTEND_BASE_URL=https://ats.trihdiconsulting.com
# ... other production values
```

### Frontend: `frontend/.env.production`
```env
VITE_API_BASE=https://ats.trihdiconsulting.com/api
```

### Caddy: `C:\recent\hirepy\Caddyfile`
- ✅ SSL automatically configured
- ✅ Reverse proxy to backend
- ✅ Serves frontend static files

## 🛠️ Common Operations

### Restart Backend
```bash
pm2 restart hirepy-backend
```

### View Logs
```bash
pm2 logs hirepy-backend        # Backend logs
type C:\recent\hirepy\caddy\logs\access.log  # Caddy logs
```

### Update Application
```bash
# After code changes
cd C:\recent\hirepy\hirepy
START_DEPLOYMENT.bat
```

### Stop Everything
```bash
pm2 stop all
# Then stop Caddy (Ctrl+C in Caddy terminal)
```

## 🔐 SSL Certificate

Caddy automatically:
- ✅ Obtains SSL certificate from Let's Encrypt
- ✅ Renews certificates automatically
- ✅ Redirects HTTP → HTTPS

No manual SSL configuration needed!

## 📊 Monitoring

### PM2 Dashboard
```bash
pm2 monit
```

### Check Status
```bash
pm2 status
pm2 list
```

### Logs Location
- PM2 Backend: `logs/pm2-backend-*.log`
- Caddy Access: `C:\recent\hirepy\caddy\logs\access.log`
- Caddy Error: `C:\recent\hirepy\caddy\logs\error.log`

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend not starting | Check `pm2 logs`, verify `.env` file |
| SSL certificate error | Verify DNS points to server IP |
| 502 Bad Gateway | Check if backend is running: `pm2 status` |
| Frontend API errors | Verify backend URL in `.env.production` |

## 📞 Support Files

- `DEPLOYMENT.md` - Detailed deployment guide
- `QUICK_START.md` - Quick start instructions
- `DEPLOY_CHECKLIST.md` - Deployment checklist
- `VERIFY_DEPLOYMENT.bat` - Verification script

---

**Everything is ready!** Just run `START_DEPLOYMENT.bat` and then start Caddy! 🎉

