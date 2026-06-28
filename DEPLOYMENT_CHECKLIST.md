# 🚀 Production Deployment Checklist

**Project**: Restaurant Booking AI Chat Bot  
**Date**: June 14, 2026  
**Version**: 1.0

---

## 📋 Pre-Deployment Phase

### Infrastructure Planning

- [ ] **Server Selection**
  - [ ] Choose cloud provider (AWS, DigitalOcean, Azure, etc.)
  - [ ] Select server specs: **Recommended minimum**
    - [ ] CPU: 2+ cores
    - [ ] RAM: 4GB minimum (8GB recommended)
    - [ ] Storage: 50GB+ SSD
    - [ ] Bandwidth: Unlimited or 1TB+/month
  - [ ] Select server region (closest to users)
  - [ ] Document server IP address: ******\_\_\_\_******

- [ ] **Domain Setup**
  - [ ] Register domain name
  - [ ] Update DNS A records to server IP
  - [ ] Update DNS MX records (if sending emails)
  - [ ] Verify DNS propagation: `nslookup your-domain.com`
  - [ ] Domain: **********\_\_\_\_**********

- [ ] **SSL Certificate**
  - [ ] Obtain SSL certificate (Let's Encrypt - free)
  - [ ] Or purchase SSL certificate
  - [ ] Store certificate safely

### Security Planning

- [ ] **Access Control**
  - [ ] Generate SSH keys for team members
  - [ ] Setup SSH access: `ssh-copy-id -i ~/.ssh/id_rsa root@server-ip`
  - [ ] Disable password-based SSH login
  - [ ] Configure firewall rules

- [ ] **Secrets Management**
  - [ ] Generate strong passwords:
    ```bash
    python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
    ```
  - [ ] Collect all API keys securely
  - [ ] Create `.env` file template
  - [ ] Store secrets safely (password manager, vault, etc.)

---

## 🖥️ Server Setup Phase

### Step 1: Provision Server

- [ ] **Create Server Instance**
  - [ ] Launch Ubuntu 22.04 LTS instance
  - [ ] Configure security groups/firewall
  - [ ] Enable automatic backups
  - [ ] Test SSH access

### Step 2: Run Server Setup Script

```bash
# SSH into server
ssh root@your-server-ip

# Download setup script
curl -O https://raw.githubusercontent.com/your-repo/scripts/server-setup.sh

# Make executable and run
chmod +x server-setup.sh
./server-setup.sh

# Verify installation
docker --version
docker-compose --version
```

- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Application user created
- [ ] Application directory created
- [ ] Nginx installed
- [ ] Firewall configured
- [ ] Backup script created

### Step 3: Configure Environment

```bash
# Copy .env template
cp /opt/apps/restaurant-booking/.env.template /opt/apps/restaurant-booking/backend/.env

# Edit environment variables
nano /opt/apps/restaurant-booking/backend/.env
```

- [ ] All database credentials set
- [ ] All API keys configured
- [ ] N8N webhook secrets set
- [ ] Telegram bot token configured
- [ ] Payment credentials set
- [ ] Email configuration done
- [ ] Security keys generated

### Step 4: Setup SSL Certificate

```bash
# Get certificate from Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Verify certificate
sudo ls -la /etc/letsencrypt/live/your-domain.com/
```

- [ ] SSL certificate obtained
- [ ] Certificate paths verified
- [ ] Auto-renewal setup

### Step 5: Configure Nginx

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/restaurant-booking

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

- [ ] Nginx config created
- [ ] SSL certificates configured
- [ ] Reverse proxy configured
- [ ] Nginx restarted successfully

---

## 🚀 Jenkins Setup Phase

### Step 1: Deploy Jenkins

**Option A: On Same Server**

```bash
chmod +x /path/to/jenkins-setup.sh
sudo ./jenkins-setup.sh
```

**Option B: On Separate Server**

- [ ] Launch separate Jenkins server
- [ ] Run jenkins-setup.sh on Jenkins server

- [ ] Java installed
- [ ] Jenkins installed
- [ ] Jenkins running on port 8080
- [ ] Initial admin password obtained

### Step 2: Initial Jenkins Configuration

1. [ ] Access Jenkins: `http://your-jenkins-ip:8080`
2. [ ] Paste initial admin password
3. [ ] Select "Install suggested plugins"
4. [ ] Create first admin user
5. [ ] Configure Jenkins URL
6. [ ] Configure system mail settings

### Step 3: Install Required Plugins

- [ ] Docker Pipeline
- [ ] Docker
- [ ] Git
- [ ] GitHub (or GitLab)
- [ ] Credentials Binding
- [ ] Environment Injector
- [ ] Pipeline Model Definition
- [ ] Slack (optional - for notifications)
- [ ] Email Extension (optional)

### Step 4: Add Credentials

- [ ] **SSH Key to Deployment Server**
  - [ ] Manage Jenkins → Manage Credentials
  - [ ] ID: `server-ssh-key`
  - [ ] Type: SSH Username with private key
  - [ ] Username: `root`
  - [ ] Private key: [Paste deployment server private key]

- [ ] **Git Repository Credentials** (if private repo)
  - [ ] ID: `github-credentials`
  - [ ] Type: Username with password
  - [ ] Username: [Your GitHub username]
  - [ ] Password: [Personal access token]

- [ ] **Docker Hub Credentials** (if using registry)
  - [ ] ID: `docker-hub-credentials`
  - [ ] Type: Username with password

### Step 5: Setup GitHub Webhook

1. [ ] GitHub Repo → Settings → Webhooks
2. [ ] Add webhook
3. [ ] Payload URL: `http://your-jenkins-ip:8080/github-webhook/`
4. [ ] Content type: `application/json`
5. [ ] Events: `Push events`
6. [ ] Active: ✓ Checked

- [ ] Webhook configured and tested

### Step 6: Create Pipeline Job

1. [ ] Jenkins Dashboard → New Item
2. [ ] Name: `restaurant-booking-deploy`
3. [ ] Type: Pipeline
4. [ ] Pipeline → Script from SCM
5. [ ] SCM: Git
6. [ ] Repository URL: Your repo URL
7. [ ] Branch: `*/main`
8. [ ] Script Path: `Jenkinsfile`

- [ ] Pipeline job created
- [ ] Can trigger builds manually

---

## 📦 Application Deployment Phase

### Step 1: Clone Repository

```bash
cd /opt/apps/restaurant-booking/backend
git clone <your-repo-url> .
```

- [ ] Repository cloned
- [ ] All files present

### Step 2: Verify Docker Images

```bash
cd /opt/apps/restaurant-booking/backend
docker-compose build --no-cache
docker images | grep restaurant
```

- [ ] Docker images built successfully

### Step 3: Deploy Containers

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

- [ ] Database container running
- [ ] Backend container running
- [ ] N8N container running

### Step 4: Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

- [ ] Database migrations completed
- [ ] Static files collected

### Step 5: Create Superuser (Admin)

```bash
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

- [ ] Superuser created
- [ ] Admin email: ********\_\_\_********
- [ ] Username: ********\_\_\_********

### Step 6: Verify Services

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test backend
curl http://localhost:8001/api/

# Test N8N
curl http://localhost:5678/

# Test database
docker-compose -f docker-compose.prod.yml exec db pg_isready
```

- [ ] Backend responding on port 8001
- [ ] N8N responding on port 5678
- [ ] Database connection working
- [ ] No errors in logs

### Step 7: Test Through Nginx/Domain

```bash
# Test through domain
curl https://your-domain.com/api/

# Check SSL
curl -I https://your-domain.com
```

- [ ] Accessible through domain
- [ ] SSL certificate valid
- [ ] Nginx reverse proxy working

---

## 📱 Frontend Deployment Phase

### Vercel Deployment

- [ ] **Repository Setup**
  - [ ] Push frontend code to GitHub/GitLab
  - [ ] Repository is public or Vercel has access

- [ ] **Create Vercel Project**

  ```bash
  cd frontend
  npm install -g vercel
  vercel login
  vercel
  ```

  - [ ] Vercel project created
  - [ ] Deployment URL: ********\_\_\_\_********

- [ ] **Environment Variables**
  - [ ] Set `VITE_API_URL` to `https://your-domain.com/api`
  - [ ] Set `VITE_WEBSOCKET_URL` to `https://your-domain.com`

- [ ] **Configure Git Integration**
  - [ ] Vercel → Git Integration
  - [ ] Select main branch
  - [ ] Production branch: `main`
  - [ ] Auto-deploy on push: ✓ Enabled

- [ ] **Test Frontend**
  - [ ] Access Vercel URL
  - [ ] Login works
  - [ ] API calls work
  - [ ] No console errors

---

## 🔄 CI/CD Pipeline Validation Phase

### Step 1: Test Manual Deployment

- [ ] **Trigger Jenkins Job Manually**

  ```
  Jenkins → restaurant-booking-deploy → Build Now
  ```

  - [ ] Build succeeds
  - [ ] All stages complete
  - [ ] Deployment successful

- [ ] **Check Application After Deployment**
  - [ ] Backend running: `curl https://your-domain.com/api/health`
  - [ ] N8N running: Check logs
  - [ ] Database migrated: Check tables
  - [ ] No errors in logs

### Step 2: Test Automated Pipeline

- [ ] **Make Code Change**

  ```bash
  git add .
  git commit -m "Test CI/CD pipeline"
  git push origin main
  ```

  - [ ] GitHub webhook triggered Jenkins
  - [ ] Jenkins build started automatically
  - [ ] All tests passed
  - [ ] Deployment completed

- [ ] **Verify Application After Auto-Deploy**
  - [ ] Check backend logs for errors
  - [ ] Verify changes deployed

---

## 🔐 Security & Monitoring Phase

### Step 1: Security Hardening

```bash
# Update fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

- [ ] Fail2ban installed
- [ ] SSH brute-force protection enabled

```bash
# Harden SSH
sudo nano /etc/ssh/sshd_config
# Set:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
sudo systemctl restart sshd
```

- [ ] SSH hardened
- [ ] Password login disabled

- [ ] **Database Security**
  - [ ] Strong database password set
  - [ ] Database only accessible from localhost
  - [ ] Database backups configured

### Step 2: Setup Monitoring

- [ ] **Container Monitoring**

  ```bash
  # View logs
  docker-compose -f docker-compose.prod.yml logs -f
  ```

- [ ] **Setup Log Rotation**
  - [ ] Configured in /etc/logrotate.d/restaurant-booking
  - [ ] Old logs rotate automatically

- [ ] **Health Checks**
  - [ ] All containers have health checks
  - [ ] Health check script created
  - [ ] Cron job for health monitoring

### Step 3: Backup Configuration

- [ ] **Database Backups**

  ```bash
  # Test backup
  /opt/apps/restaurant-booking/backup.sh
  ```

  - [ ] Backup script runs successfully
  - [ ] Backups stored in /opt/apps/restaurant-booking/data/backups
  - [ ] Cron job configured for daily backups at 2 AM

- [ ] **Backup Testing**
  - [ ] Try restoring from backup to verify integrity

---

## 📊 Performance Tuning Phase

- [ ] **Django Settings**
  - [ ] DEBUG = False in production
  - [ ] ALLOWED_HOSTS configured
  - [ ] CSRF_TRUSTED_ORIGINS configured
  - [ ] Cache backend configured
  - [ ] Session backend configured

- [ ] **Database Performance**
  - [ ] Indexes created on frequently queried columns
  - [ ] Connection pooling configured

- [ ] **Nginx Performance**
  - [ ] Compression enabled (gzip)
  - [ ] Client max body size set appropriately
  - [ ] Keepalive configured

- [ ] **Docker Performance**
  - [ ] Resource limits set
  - [ ] Appropriate number of worker processes
  - [ ] Container health checks working

---

## 📞 Documentation & Handover Phase

### Documentation

- [ ] **Deployment Documentation**
  - [ ] DEPLOYMENT_GUIDE.md completed
  - [ ] Server IP documented: ******\_\_\_******
  - [ ] Domain documented: ******\_\_\_******
  - [ ] SSH access documented

- [ ] **API Documentation**
  - [ ] Admin access available at: `https://your-domain.com/admin`
  - [ ] Swagger docs available at: `https://your-domain.com/api/swagger`
  - [ ] API keys shared securely

- [ ] **N8N Documentation**
  - [ ] N8N admin access configured
  - [ ] Webhooks documented
  - [ ] Workflow backups created

### Team Training

- [ ] **DevOps Team**
  - [ ] How to view logs: `docker-compose logs -f`
  - [ ] How to restart services: `docker-compose restart <service>`
  - [ ] How to perform backups
  - [ ] How to monitor health

- [ ] **Development Team**
  - [ ] CI/CD pipeline workflow explained
  - [ ] How to test locally before pushing
  - [ ] How to monitor deployments in Jenkins

---

## ✅ Post-Deployment Monitoring Phase

### Week 1: Active Monitoring

- [ ] **Daily Checks**
  - [ ] Check application logs for errors
  - [ ] Check server resource usage (CPU, RAM, disk)
  - [ ] Monitor error rates in backend logs
  - [ ] Check database performance

- [ ] **Weekly Reports**
  - [ ] Backup completion status
  - [ ] Performance metrics
  - [ ] Security alerts
  - [ ] User issues (if any)

### Ongoing Maintenance

- [ ] **Monthly Tasks**
  - [ ] Review and optimize slow queries
  - [ ] Update Docker base images
  - [ ] Test backup restoration
  - [ ] Security updates and patches

- [ ] **Quarterly Tasks**
  - [ ] Capacity planning review
  - [ ] Disaster recovery testing
  - [ ] Security audit
  - [ ] Performance optimization review

---

## 🎯 Deployment Sign-Off

| Role            | Name | Date | Signature |
| --------------- | ---- | ---- | --------- |
| Project Manager |      |      |           |
| DevOps Lead     |      |      |           |
| Backend Lead    |      |      |           |
| Frontend Lead   |      |      |           |
| Security Lead   |      |      |           |

---

## 📚 Useful Commands Reference

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Restart a service
docker-compose -f docker-compose.prod.yml restart backend

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Stop all containers
docker-compose -f docker-compose.prod.yml down

# Check container status
docker-compose -f docker-compose.prod.yml ps

# View resource usage
docker stats

# SSH to server
ssh root@your-server-ip

# View Nginx logs
sudo tail -f /var/log/nginx/restaurant-booking_access.log

# Renew SSL certificate
sudo certbot renew

# Check certificate expiration
sudo certbot certificates

# Restart Nginx
sudo systemctl restart nginx

# Check Jenkins build logs
curl http://your-jenkins-ip:8080/job/restaurant-booking-deploy/lastBuild/consoleText
```

---

## 📞 Support Contacts

| Service           | Contact | Availability |
| ----------------- | ------- | ------------ |
| Server Hosting    |         |              |
| Domain Registrar  |         |              |
| CI/CD Support     |         |              |
| API Support       |         |              |
| Emergency Contact |         |              |

---

**Last Updated**: June 14, 2026  
**Next Review Date**: ******\_******
