# 🚀 Quick Deployment Reference

**Quick links for deployment setup**

---

## 📋 Files Created

### 1. Deployment Guides

- **DEPLOYMENT_GUIDE.md** - Complete step-by-step deployment guide
- **DEPLOYMENT_CHECKLIST.md** - Detailed checklist for production deployment

### 2. Configuration Files

- **Jenkinsfile** - CI/CD pipeline configuration (place in repo root)
- **backend/docker-compose.prod.yml** - Production Docker Compose

### 3. Setup Scripts

- **scripts/server-setup.sh** - Server initialization (Docker, Nginx, etc.)
- **scripts/jenkins-setup.sh** - Jenkins installation and configuration

---

## ⚡ Quick Start (5 Minutes)

### 1. Provision Server

```bash
# Buy server on AWS/DigitalOcean/Azure
# Choose: Ubuntu 22.04 LTS, 2+ cores, 4GB+ RAM

# Get server IP address
# Setup DNS: your-domain.com → server-ip
```

### 2. Run Server Setup

```bash
ssh root@your-server-ip

curl -O https://raw.githubusercontent.com/your-username/demo-chat-bot/main/scripts/server-setup.sh
chmod +x server-setup.sh
./server-setup.sh
```

### 3. Setup Environment

```bash
# Create .env file
cp /opt/apps/restaurant-booking/.env.template /opt/apps/restaurant-booking/backend/.env

# Edit with your secrets
nano /opt/apps/restaurant-booking/backend/.env

# Generate secure passwords
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Setup SSL

```bash
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
```

### 5. Configure Nginx

Edit `/etc/nginx/sites-available/restaurant-booking` with SSL paths and domain name.

### 6. Deploy Backend

```bash
cd /opt/apps/restaurant-booking/backend
git clone <your-repo> .
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### 7. Setup Jenkins (Separate Server)

```bash
ssh root@jenkins-server-ip
curl -O https://raw.githubusercontent.com/your-username/demo-chat-bot/main/scripts/jenkins-setup.sh
chmod +x jenkins-setup.sh
sudo ./jenkins-setup.sh
```

### 8. Configure Jenkins Pipeline

- Access: `http://jenkins-ip:8080`
- Create job: `restaurant-booking-deploy`
- Add credentials: SSH key, Git credentials
- Copy Jenkinsfile to repo root
- Add GitHub webhook

### 9. Deploy Frontend

```bash
cd frontend
npm install -g vercel
vercel login
vercel
# Set env variables: VITE_API_URL, VITE_WEBSOCKET_URL
```

---

## 🔑 Required Information

Before deployment, gather:

```
┌─────────────────────────────────────────────────┐
│ PRODUCTION CREDENTIALS CHECKLIST                │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🖥️ SERVER INFORMATION                          │
│ ├─ Server IP: ________________________         │
│ ├─ Domain: ________________________             │
│ ├─ Server User: root                           │
│ └─ SSH Key: [Generate new key]                 │
│                                                 │
│ 🔐 DATABASE                                     │
│ ├─ DB Name: restaurant_booking_prod           │
│ ├─ DB User: postgres                           │
│ ├─ DB Password: ________________________       │
│ └─ DB Host: db (internal)                      │
│                                                 │
│ 🔑 DJANGO SECRETS                              │
│ ├─ SECRET_KEY: ________________________        │
│ ├─ DEBUG: False                                │
│ ├─ ALLOWED_HOSTS: your-domain.com             │
│ └─ CSRF_TRUSTED_ORIGINS: https://your-domain │
│                                                 │
│ 📧 EMAIL (Notifications)                       │
│ ├─ SMTP_HOST: smtp.gmail.com                  │
│ ├─ SMTP_USER: ________________________         │
│ ├─ SMTP_PASSWORD: ________________________     │
│ └─ SMTP_PORT: 587                              │
│                                                 │
│ 🤖 API KEYS                                     │
│ ├─ OPENAI_API_KEY: sk-...                      │
│ ├─ ANTHROPIC_API_KEY: sk-ant-...              │
│ ├─ GEMINI_API_KEY: ________________________    │
│ └─ TELEGRAM_BOT_TOKEN: ________________________ │
│                                                 │
│ 💳 PAYMENT (SePay)                             │
│ ├─ SEPAY_MERCHANT_ID: ________________________ │
│ ├─ SEPAY_SECRET_KEY: ________________________  │
│ └─ SEPAY_ENVIRONMENT: production              │
│                                                 │
│ 🔔 N8N WEBHOOKS                                │
│ ├─ N8N_WEBHOOK_SECRET: ________________________│
│ └─ TELEGRAM_CHAT_ID: ________________________  │
│                                                 │
│ 🚀 CI/CD                                        │
│ ├─ Jenkins Server IP: ________________________ │
│ ├─ GitHub Personal Token: ________________________
│ └─ Docker Hub (optional): ________________________
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Health Check Commands

```bash
# SSH into server
ssh root@your-server-ip

# Check all containers
cd /opt/apps/restaurant-booking/backend
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check backend health
curl http://localhost:8001/api/health

# Check database
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Check N8N
curl http://localhost:5678/healthz

# Check Nginx
sudo systemctl status nginx

# View system resources
htop

# Check disk space
df -h
```

---

## 📊 Monitoring Dashboard

Set up monitoring with these commands:

```bash
# Real-time container stats
watch docker stats

# Application logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100 backend

# Database logs
docker-compose -f docker-compose.prod.yml logs -f db

# System load
uptime
top -b -n 1
```

---

## 🔄 Common Tasks

### Deploy New Version

```bash
# On deployment server
cd /opt/apps/restaurant-booking/backend

# Pull latest code
git pull origin main

# Restart containers (or trigger Jenkins)
docker-compose -f docker-compose.prod.yml restart backend

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### View Admin Panel

```
https://your-domain.com/admin
Username: [superuser created in step 6]
```

### Restart N8N

```bash
docker-compose -f docker-compose.prod.yml restart n8n
```

### Database Backup

```bash
/opt/apps/restaurant-booking/backup.sh
```

### View Backups

```bash
ls -lah /opt/apps/restaurant-booking/data/backups/
```

---

## 🚨 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check if port is in use
lsof -i :8001

# Rebuild container
docker-compose -f docker-compose.prod.yml build --no-cache backend
```

### Database connection error

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps db

# Check environment variables
grep POSTGRES /opt/apps/restaurant-booking/backend/.env

# Test database connection
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"
```

### Nginx SSL errors

```bash
# Check certificate
sudo certbot certificates

# Verify Nginx config
sudo nginx -t

# Check certificate paths in Nginx config
sudo grep ssl_ /etc/nginx/sites-available/restaurant-booking
```

### Jenkins build fails

```bash
# Check Jenkins logs
sudo tail -f /var/log/jenkins/jenkins.log

# Check build console
http://your-jenkins-ip:8080/job/restaurant-booking-deploy/lastBuild/console

# Verify SSH credentials
ssh -i /var/lib/jenkins/.ssh/id_rsa root@your-server-ip "echo Connection works"
```

---

## 📱 Frontend (Vercel) Updates

Frontend auto-deploys when you push to `main` branch:

```bash
cd frontend
git add .
git commit -m "Feature: Add new feature"
git push origin main
# Vercel automatically deploys! ✅
```

Check deployment:

- Vercel Dashboard: https://vercel.com/dashboard
- Frontend URL: https://your-vercel-project.vercel.app
- Production URL: your domain (configured in Vercel)

---

## 📚 Documentation

- **Full Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **N8N Setup**: `docs/N8N_SETUP_GUIDE.md`
- **N8N Quick Start**: `docs/N8N_QUICKSTART.md`
- **How to Run N8N**: `docs/N8N_HOW_TO_RUN.md`

---

## 🎯 Success Indicators

After deployment, verify:

✅ Backend accessible: `https://your-domain.com/api/`  
✅ Admin panel accessible: `https://your-domain.com/admin/`  
✅ N8N webhooks working (check logs)  
✅ Frontend deployed: `https://your-vercel-project.vercel.app`  
✅ SSL certificate valid  
✅ Database migrations completed  
✅ All containers running  
✅ Backups created  
✅ Jenkins pipeline working  
✅ GitHub webhook triggering builds

---

## 📞 Support Resources

- **Jenkins Docs**: https://www.jenkins.io/doc/
- **Docker Docs**: https://docs.docker.com/
- **Django Docs**: https://docs.djangoproject.com/
- **N8N Docs**: https://docs.n8n.io/
- **Vercel Docs**: https://vercel.com/docs

---

## 🔒 Security Checklist After Deployment

- [ ] Change default passwords
- [ ] Enable SSH key-only authentication
- [ ] Configure firewall (UFW)
- [ ] Install fail2ban for brute-force protection
- [ ] Setup SSL certificates
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Setup rate limiting
- [ ] Enable audit logging
- [ ] Perform security audit
- [ ] Setup monitoring alerts
- [ ] Document security procedures

---

**Last Updated**: June 14, 2026  
**Status**: ✅ Ready for Production
