# 🚀 Production Deployment Guide

Complete guide for deploying the Restaurant Booking AI Chat Bot to production with Jenkins CI/CD.

---

## 📚 Documentation Index

1. **QUICK_DEPLOYMENT_REFERENCE.md** - Quick reference (5-minute quick start)
2. **DEPLOYMENT_GUIDE.md** - Comprehensive step-by-step guide
3. **DEPLOYMENT_CHECKLIST.md** - Detailed checklist for production
4. **This file** - Overview and architecture

---

## 🎯 Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      YOUR DOMAIN                              │
│                  your-domain.com                              │
└───────────────┬──────────────────────────────────────────────┘
                │ HTTPS
                ↓
        ┌───────────────────┐
        │   Nginx Proxy     │
        │   (SSL/TLS)       │
        └────┬──────┬───────┘
             │      │
         ┌───┘      └───┐
         ↓              ↓
    ┌─────────┐    ┌─────────┐
    │ Backend │    │   N8N   │
    │ (8001)  │    │ (5678)  │
    └────┬────┘    └────┬────┘
         │              │
         └──────┬───────┘
                ↓
        ┌──────────────┐
        │  PostgreSQL  │
        │  (Database)  │
        └──────────────┘

Frontend: Vercel (Auto-deploy from GitHub)
CI/CD: Jenkins (Auto-build & deploy on push)
```

---

## 🚀 Deployment Options

### Option 1: Jenkins Server (Recommended for Teams)

**Best for**: Teams with dedicated DevOps engineer

```
Developer pushes code → GitHub → Webhook → Jenkins → Deploy Server
```

**Setup Time**: 2-3 hours  
**Complexity**: Medium  
**Cost**: $5-10/month Jenkins server + $5-20/month deploy server

### Option 2: GitHub Actions (Easiest for Solo Dev)

**Best for**: Solo developers or small teams

```
Developer pushes code → GitHub → Actions → Deploy Server
```

**Setup Time**: 30 minutes  
**Complexity**: Low  
**Cost**: Free (up to 2000 minutes/month) + $5-20/month deploy server

### Option 3: Manual Deployment (Not Recommended)

```
Developer SSH → pull code → docker-compose up
```

**Setup Time**: 5 minutes  
**Complexity**: Very Low  
**Risk**: High (manual errors)

---

## 📋 Server Requirements

### Minimum Configuration

- **OS**: Ubuntu 22.04 LTS
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 50GB SSD
- **Network**: 1TB+/month bandwidth

### Recommended Configuration

- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 100GB SSD
- **Network**: Unlimited

### Cloud Provider Options

| Provider         | Cost      | Setup  | Notes                           |
| ---------------- | --------- | ------ | ------------------------------- |
| **DigitalOcean** | $5-12/mo  | Easy   | Simple, good for small projects |
| **AWS EC2**      | $10-30/mo | Medium | Powerful, pay as you go         |
| **Azure**        | $15-40/mo | Medium | Good for enterprise             |
| **Linode**       | $5-25/mo  | Easy   | Good performance                |
| **Hetzner**      | €3-8/mo   | Easy   | Cheapest option                 |

---

## 🔧 What Each Component Does

### Backend (Django)

- REST API endpoints
- Database queries
- N8N webhook handlers
- Authentication & authorization
- File uploads

**Technology**: Python, Django, Gunicorn, PostgreSQL  
**Port**: 8001 (local) → 443 (public via Nginx)

### N8N (Workflow Engine)

- Telegram bot integration
- Admin notifications
- Webhook handlers
- Email notifications

**Technology**: Node.js, N8N  
**Port**: 5678 (local) → 443 (public via Nginx)

### PostgreSQL (Database)

- User accounts
- Restaurant bookings
- Payment records
- Notifications log

**Technology**: PostgreSQL with pgvector extension  
**Port**: 5432 (private, not exposed)

### Frontend (React)

- User interface
- Customer dashboard
- Booking management
- Admin panel

**Technology**: React, Vite  
**Deployment**: Vercel (auto-deploy)  
**URL**: Vercel URL or custom domain

### Jenkins (CI/CD)

- Automated testing
- Docker image building
- Automated deployment
- Health checks

**Technology**: Jenkins, Docker  
**Port**: 8080 (internal)

---

## 📦 Files Explained

### New Deployment Files

| File                              | Purpose                     | When to Use              |
| --------------------------------- | --------------------------- | ------------------------ |
| **Jenkinsfile**                   | CI/CD pipeline config       | If using Jenkins         |
| **.github/workflows/deploy.yml**  | GitHub Actions config       | If using GitHub Actions  |
| **docker-compose.prod.yml**       | Production container setup  | For all deployments      |
| **scripts/server-setup.sh**       | Initialize server           | First time server setup  |
| **scripts/jenkins-setup.sh**      | Install Jenkins             | First time Jenkins setup |
| **DEPLOYMENT_GUIDE.md**           | Step-by-step instructions   | Main reference           |
| **DEPLOYMENT_CHECKLIST.md**       | Pre-deployment verification | Before going live        |
| **QUICK_DEPLOYMENT_REFERENCE.md** | Quick reference             | During deployment        |

### Existing Files (No Changes Needed)

- **backend/Dockerfile** - Already production-ready
- **backend/docker-compose.yml** - For local development
- **backend/requirements.txt** - Python dependencies
- **backend/manage.py** - Django management tool

---

## 🔄 Deployment Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Day 1: Initial Setup                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Buy & provision server (2 min)                            │
│ 2. Run server-setup.sh (5 min)                               │
│ 3. Setup SSL certificate (2 min)                             │
│ 4. Configure Nginx (2 min)                                   │
│ 5. Setup Jenkins server (3 min)                              │
│ 6. Configure Jenkins (10 min)                                │
│ 7. Clone repo & deploy (5 min)                               │
│ TOTAL TIME: ~30 minutes                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Day 2+: New Deployments                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Developer pushes code to main branch                      │
│ 2. GitHub webhook triggers Jenkins                           │
│ 3. Jenkins builds Docker images                              │
│ 4. Jenkins runs tests                                        │
│ 5. If tests pass → Deploy to server                          │
│ 6. Run database migrations                                   │
│ 7. Health checks verify deployment                           │
│ 8. Notification sent to team                                 │
│ TIME: ~2-3 minutes per deployment                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Step-by-Step (High Level)

### Phase 1: Preparation (30 min)

1. Gather all API keys and credentials
2. Choose server provider and buy server
3. Register domain and setup DNS

### Phase 2: Server Setup (15 min)

1. SSH into server
2. Run `server-setup.sh`
3. Create `.env` file with secrets
4. Setup SSL certificate
5. Configure Nginx

### Phase 3: Jenkins Setup (30 min)

1. Setup Jenkins server (separate or same)
2. Install required plugins
3. Add credentials (SSH, Git)
4. Create pipeline job
5. Configure GitHub webhook

### Phase 4: First Deployment (20 min)

1. Clone repository
2. Build Docker images
3. Deploy containers
4. Run migrations
5. Test everything

### Phase 5: Automation (5 min)

1. Push code to main branch
2. Jenkins auto-deploys
3. Verify deployment success

**Total Setup Time**: ~2 hours  
**Deployment Time (after setup)**: ~3 minutes per deployment

---

## 🔐 Security Considerations

### Before Going Live

- [ ] Change all default passwords
- [ ] Setup SSH key-only authentication (no passwords)
- [ ] Enable firewall (UFW)
- [ ] Setup fail2ban (brute-force protection)
- [ ] Enable SSL/TLS on all connections
- [ ] Set `DEBUG = False` in Django
- [ ] Configure ALLOWED_HOSTS correctly
- [ ] Setup rate limiting on API
- [ ] Enable CORS only for frontend domain
- [ ] Regular security updates

### Post-Deployment Monitoring

- [ ] Monitor error logs daily
- [ ] Check server resource usage
- [ ] Verify backups are running
- [ ] Test backup restoration (weekly)
- [ ] Monitor API response times
- [ ] Check for unusual traffic patterns
- [ ] Regular security audits

---

## 📊 Performance Optimization

### Backend Optimization

- Use connection pooling for database
- Cache frequently accessed data
- Implement pagination on list endpoints
- Use async tasks for heavy operations
- Monitor slow queries

### Database Optimization

- Add indexes on frequently queried columns
- Regular VACUUM and ANALYZE
- Monitor query performance
- Implement archival for old data

### Server Optimization

- Enable gzip compression in Nginx
- Use CDN for static files (optional)
- Implement rate limiting
- Monitor resource usage
- Auto-scale if needed

---

## 🚨 Troubleshooting Guide

### Most Common Issues

**Q: Containers won't start**  
A: Check logs: `docker-compose -f docker-compose.prod.yml logs`

**Q: Database connection refused**  
A: Verify POSTGRES\_\* environment variables match `.env` file

**Q: SSL certificate errors**  
A: Verify certificate path in Nginx config, renew if expired

**Q: Jenkins can't deploy**  
A: Check SSH credentials, verify keys are added to server

**Q: Nginx returns 502**  
A: Backend container not running, check logs and restart

See **DEPLOYMENT_GUIDE.md** for detailed troubleshooting.

---

## 🔄 Zero-Downtime Deployment (Advanced)

For seamless updates without service interruption:

```bash
# 1. Backup current deployment
docker-compose -f docker-compose.prod.yml down -v

# 2. Start new version
docker-compose -f docker-compose.prod.yml up -d

# 3. Run migrations
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

# 4. Nginx automatically routes to new version
```

Or implement:

- Blue-green deployment (two server instances)
- Canary deployment (gradual rollout)
- Rolling updates (update one container at a time)

---

## 📱 Frontend Deployment

Frontend auto-deploys to Vercel on push to main:

```bash
# Just commit and push
git add .
git commit -m "Update UI"
git push origin main

# Vercel automatically builds and deploys! ✅
```

Monitor at: https://vercel.com/dashboard

---

## 💾 Backup Strategy

### Automated Daily Backups

- Database backup: 2 AM daily
- N8N data backup: 2 AM daily
- Stored in: `/opt/apps/restaurant-booking/data/backups/`
- Retention: 7 days

### Manual Backup

```bash
/opt/apps/restaurant-booking/backup.sh
```

### Restore from Backup

```bash
# Database restore
gunzip < /opt/apps/restaurant-booking/data/backups/db_backup_*.sql.gz | psql -U postgres

# N8N restore
docker cp /opt/apps/restaurant-booking/data/backups/n8n_backup_*/ ai_chat_bot_n8n:/home/node/.n8n
```

---

## 📈 Scaling Strategy

### Phase 1: Single Server (Current)

- All services on one 2-core server
- Suitable for: < 1000 daily users
- Cost: ~$10-20/month

### Phase 2: Separate Database

- Database on managed service (RDS, Azure DB)
- Backend on compute instance
- Suitable for: 1000-5000 daily users
- Cost: ~$30-50/month

### Phase 3: Load Balanced

- Multiple backend instances
- Load balancer (Nginx, HAProxy)
- Managed database
- Suitable for: 5000-50000 daily users
- Cost: ~$100-200/month

### Phase 4: Kubernetes/Container Orchestration

- Kubernetes cluster
- Auto-scaling
- Advanced monitoring
- Suitable for: 50000+ daily users
- Cost: ~$200-500+/month

---

## 📞 Support & Resources

### Documentation

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Docker Documentation](https://docs.docker.com/)
- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [N8N Documentation](https://docs.n8n.io/)

### Team Resources

- Project GitHub: [your-repo-url]
- Production Server: [your-domain.com]
- Jenkins Dashboard: [your-jenkins-ip:8080]
- Admin Panel: [your-domain.com/admin]

### Emergency Contacts

- DevOps Lead: [contact info]
- Backend Lead: [contact info]
- On-Call Support: [contact info]

---

## ✅ Deployment Verification Checklist

After deployment, verify:

- [ ] Backend API responding: `curl https://your-domain.com/api/`
- [ ] Admin panel accessible: `https://your-domain.com/admin/`
- [ ] Frontend loaded: `https://your-domain.com/`
- [ ] SSL certificate valid: Check browser
- [ ] Database connected: Check admin panel
- [ ] N8N webhooks working: Check logs
- [ ] Backup completed: Check `/data/backups/`
- [ ] All containers running: `docker-compose ps`
- [ ] No errors in logs: `docker-compose logs`
- [ ] Health checks passing: Check endpoints

---

## 🎓 Training for Team

### For DevOps Engineer

- Learn Jenkinsfile pipeline syntax
- Docker and Docker Compose
- Nginx configuration
- SSL/TLS management
- Server monitoring

### For Backend Developer

- How to read deployment logs
- How to trigger deployments
- Database migration process
- Environment variable management

### For Frontend Developer

- Vercel deployment process
- Environment variables in Vercel
- Build configuration
- How to trigger frontend deployment

---

## 📝 Version History

| Version | Date          | Changes                  |
| ------- | ------------- | ------------------------ |
| 1.0     | June 14, 2026 | Initial deployment guide |

---

## 📄 Related Documentation

- [N8N Setup Guide](docs/N8N_SETUP_GUIDE.md)
- [N8N How to Run](docs/N8N_HOW_TO_RUN.md)
- [N8N Quick Start](N8N_QUICKSTART.md)
- [Server Setup Guide](DEPLOYMENT_GUIDE.md)
- [Quick Reference](QUICK_DEPLOYMENT_REFERENCE.md)
- [Checklist](DEPLOYMENT_CHECKLIST.md)

---

**Last Updated**: June 14, 2026  
**Status**: ✅ Ready for Production  
**Next Review**: After first deployment
