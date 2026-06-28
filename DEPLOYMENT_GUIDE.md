# 🚀 Deploy Guide: Jenkins CI/CD + Server Deployment

**Ngày tạo**: June 14, 2026  
**Mục đích**: Deploy Backend + N8N + Database + Frontend (Vercel)

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GIT REPOSITORY                           │
│                    (GitHub/GitLab)                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓ (Webhook on push/PR)
┌─────────────────────────────────────────────────────────────────┐
│                    JENKINS SERVER                                │
│  (CI/CD Pipeline)                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Checkout   │→ │ Build      │→ │ Test       │                │
│  │ Git Repo   │  │ Docker     │  │ Code       │                │
│  └────────────┘  └────────────┘  └────────────┘                │
│         ↓              ↓              ↓                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Deploy     │→ │ Migrate    │→ │ Health     │                │
│  │ Docker     │  │ DB         │  │ Check      │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ├──→ Backend (Port 8001)
       ├──→ N8N (Port 5678)
       ├──→ PostgreSQL (Port 5432)
       └──→ Frontend → Vercel (Auto Deploy)
```

---

## 🖥️ Server Setup (Ubuntu 22.04 LTS)

### Step 1: Prerequisites Installation

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Create Application Directory

```bash
# Create directory structure
sudo mkdir -p /opt/apps/restaurant-booking
cd /opt/apps/restaurant-booking

# Set permissions
sudo chown $USER:$USER /opt/apps/restaurant-booking

# Create necessary directories
mkdir -p backend frontend logs data/.env
```

### Step 3: Setup Jenkins Server

#### Option A: Jenkins on Same Server

```bash
# Install Java
sudo apt install openjdk-11-jdk -y

# Install Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install jenkins -y

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Check initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Access: **http://your-server-ip:8080**

#### Option B: Jenkins on Separate Server (Recommended for Production)

Create separate EC2/VPS instance and install Jenkins there.

---

## 🔑 Jenkins Configuration

### Step 1: Install Required Plugins

In Jenkins Dashboard:

1. Go to: **Manage Jenkins** → **Manage Plugins**
2. Search and install:
   - `Docker Pipeline`
   - `Git`
   - `GitHub` (if using GitHub)
   - `Credentials Binding`
   - `Environment Injector`

### Step 2: Add Credentials

1. **Manage Jenkins** → **Manage Credentials** → **Add Credentials**

**Add SSH Key** (for server access):

```
Type: SSH Username with private key
ID: server-ssh-key
Username: root (or your user)
Private Key: [Paste your SSH private key]
Passphrase: [If key has passphrase]
```

**Add Git Credentials** (if private repo):

```
Type: Username with password
ID: github-credentials
Username: [Your GitHub username]
Password: [Your personal access token]
```

**Add Docker Registry Credentials** (Optional):

```
Type: Username with password
ID: docker-hub-credentials
Username: [DockerHub username]
Password: [DockerHub password]
```

---

## 📝 Jenkins Pipeline Setup

### Step 1: Create New Pipeline Job

1. Jenkins Dashboard → **New Item**
2. Enter name: `restaurant-booking-deploy`
3. Choose: **Pipeline**
4. Click **OK**

### Step 2: Pipeline Configuration

In **Pipeline** section, paste this Jenkinsfile:

```groovy
pipeline {
    agent any

    environment {
        // Server details
        SERVER_IP = '123.45.67.89'  // Change to your server IP
        SERVER_USER = 'root'         // SSH user
        APP_DIR = '/opt/apps/restaurant-booking'

        // Docker registry (optional)
        DOCKER_REGISTRY = 'your-dockerhub-username'

        // Git
        GIT_REPO = 'https://github.com/your-username/DATN-restaurant-booking-agent'
        GIT_BRANCH = 'main'

        // Credentials
        SSH_KEY = credentials('server-ssh-key')
        GIT_CRED = credentials('github-credentials')
    }

    stages {
        stage('🔍 Checkout Code') {
            steps {
                script {
                    echo '📥 Cloning repository...'
                    checkout([$class: 'GitSCM',
                        branches: [[name: "*/${GIT_BRANCH}"]],
                        userRemoteConfigs: [[url: "${GIT_REPO}"]]
                    ])
                }
            }
        }

        stage('🔨 Build Docker Images') {
            steps {
                script {
                    echo '🏗️ Building Docker images...'
                    sh '''
                        cd backend
                        docker-compose build --no-cache
                    '''
                }
            }
        }

        stage('✅ Run Tests') {
            steps {
                script {
                    echo '🧪 Running tests...'
                    sh '''
                        cd backend
                        # Run Django tests
                        docker-compose run --rm backend python manage.py test
                    '''
                }
            }
        }

        stage('📦 Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo '📤 Pushing images to Docker registry...'
                    sh '''
                        # Tag images
                        docker tag ai_chat_bot_backend:latest ${DOCKER_REGISTRY}/restaurant-booking-backend:latest
                        docker tag ai_chat_bot_n8n:latest ${DOCKER_REGISTRY}/restaurant-booking-n8n:latest

                        # Push (optional - only if you use Docker registry)
                        # docker push ${DOCKER_REGISTRY}/restaurant-booking-backend:latest
                        # docker push ${DOCKER_REGISTRY}/restaurant-booking-n8n:latest
                    '''
                }
            }
        }

        stage('🚀 Deploy to Server') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo '🌍 Deploying to production server...'
                    sh '''
                        # Copy files to server
                        scp -i ${SSH_KEY} -r backend/* ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/backend/

                        # SSH and deploy
                        ssh -i ${SSH_KEY} ${SERVER_USER}@${SERVER_IP} "
                            cd ${APP_DIR}/backend

                            # Pull latest .env (don't overwrite with git version)
                            # cp .env.prod .env

                            # Stop old containers
                            docker-compose down

                            # Start new containers
                            docker-compose up -d

                            # Run migrations
                            docker-compose exec -T backend python manage.py migrate

                            # Collect static files
                            docker-compose exec -T backend python manage.py collectstatic --noinput
                        "
                    '''
                }
            }
        }

        stage('🔗 Deploy Frontend to Vercel') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo '📱 Deploying frontend to Vercel...'
                    sh '''
                        cd frontend

                        # Deploy to Vercel (requires Vercel CLI)
                        # vercel --prod --token ${VERCEL_TOKEN}

                        echo "Frontend deployment trigger configured in Vercel webhooks"
                    '''
                }
            }
        }

        stage('🏥 Health Check') {
            steps {
                script {
                    echo '✨ Running health checks...'
                    sh '''
                        sleep 10

                        # Check if backend is running
                        BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER_IP}:8001/api/health)

                        if [ $BACKEND_STATUS -ne 200 ]; then
                            echo "❌ Backend health check failed"
                            exit 1
                        fi

                        # Check N8N
                        N8N_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER_IP}:5678)

                        if [ $N8N_STATUS -ne 200 ]; then
                            echo "⚠️ N8N may not be ready yet"
                        fi

                        echo "✅ All services healthy"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ Deployment successful!'
            // Send success notification (Slack, email, etc)
        }
        failure {
            echo '❌ Deployment failed!'
            // Send failure notification
        }
    }
}
```

### Step 3: Save and Test

1. Click **Save**
2. Click **Build Now** to test
3. Monitor build in **Console Output**

---

## 🛠️ Alternative: Jenkinsfile in Repository

For better version control, create `Jenkinsfile` in your repo root:

```bash
# Create in project root
cat > Jenkinsfile << 'EOF'
pipeline {
    agent any

    environment {
        SERVER_IP = '123.45.67.89'
        SERVER_USER = 'root'
        APP_DIR = '/opt/apps/restaurant-booking'
        SSH_KEY = credentials('server-ssh-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh '''
                    cd backend
                    docker-compose build --no-cache
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    cd backend
                    docker-compose run --rm backend python manage.py test
                '''
            }
        }

        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh '''
                    scp -i ${SSH_KEY} -r backend/* ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/backend/

                    ssh -i ${SSH_KEY} ${SERVER_USER}@${SERVER_IP} "
                        cd ${APP_DIR}/backend
                        docker-compose down
                        docker-compose up -d
                        docker-compose exec -T backend python manage.py migrate
                    "
                '''
            }
        }
    }
}
EOF

git add Jenkinsfile
git commit -m "Add Jenkins pipeline configuration"
git push origin main
```

Then in Jenkins, choose:

- Pipeline → **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: Your Git repo
- Credentials: Select your Git credentials
- Script Path: `Jenkinsfile`

---

## 🔐 Production Environment Configuration

### Step 1: Create Production .env

On your server, create `backend/.env.prod`:

```bash
ssh root@your-server-ip
cat > /opt/apps/restaurant-booking/backend/.env.prod << 'EOF'
# Database Configuration
POSTGRES_DB=restaurant_booking_prod
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django Configuration
APPLICATION_SECRET=your-very-strong-secret-key-change-this
DEBUG=False
USE_ENV_FILE=.env
WEBSITE_NAME="PSCD Japanese Dining"
WEBSITE_URL=https://your-domain.com

# N8N Configuration
N8N_ADMIN_NOTIFICATIONS_ENABLED=1
N8N_ADMIN_WEBHOOK_URL=http://n8n:5678/webhook/restaurant-admin-notify
N8N_ADMIN_WEBHOOK_SECRET=your-n8n-secret-here

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=-your-chat-id

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True

# AI API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Payment (SePay)
SEPAY_MERCHANT_ID=SP-LIVE-...
SEPAY_SECRET_KEY=spsk_live_...
SEPAY_ENVIRONMENT=production
SEPAY_SUCCESS_URL=https://your-domain.com/success.html
SEPAY_ERROR_URL=https://your-domain.com/error.html
SEPAY_CANCEL_URL=https://your-domain.com/cancel.html

# Swagger
IS_DISPLAY_SWAGGER=0

# Security
ACCESS_TOKEN_LIFETIME=24
REFRESH_TOKEN_LIFETIME=168
PASSWORD_RESET_TIMEOUT=3600
EOF

chmod 600 /opt/apps/restaurant-booking/backend/.env.prod
```

### Step 2: Update docker-compose.yml for Production

Create `backend/docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  db:
    image: ankane/pgvector
    container_name: ai_chat_bot_db
    volumes:
      - postgres_db_api_chat_bot:/var/lib/postgresql/data
    ports:
      - 5432:5432
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    restart: always
    networks:
      - api_chat_bot_network

  n8n:
    image: n8nio/n8n:latest
    container_name: ai_chat_bot_n8n
    ports:
      - 5678:5678
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_ADMIN_WEBHOOK_SECRET=${N8N_ADMIN_WEBHOOK_SECRET}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    volumes:
      - n8n_data:/home/node/.n8n
    restart: always
    depends_on:
      - db
    networks:
      - api_chat_bot_network

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai_chat_bot_backend
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - DEBUG=False
      - ALLOWED_HOSTS=your-domain.com,www.your-domain.com
      - CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
    command: gunicorn api_chat_bot.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 4 --timeout 3600
    ports:
      - 8001:8000
    depends_on:
      - db
      - n8n
    restart: always
    networks:
      - api_chat_bot_network
    env_file:
      - .env.prod

volumes:
  postgres_db_api_chat_bot:
  n8n_data:

networks:
  api_chat_bot_network:
    driver: bridge
```

### Step 3: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create config
sudo cat > /etc/nginx/sites-available/restaurant-booking << 'EOF'
upstream backend {
    server 127.0.0.1:8001;
}

upstream n8n {
    server 127.0.0.1:5678;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Backend proxy
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        client_max_body_size 100M;
    }

    # Admin panel
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # N8N webhooks
    location /webhook/ {
        proxy_pass http://n8n;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/apps/restaurant-booking/backend/staticfiles/;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/restaurant-booking /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 4: Setup SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 📱 Frontend Deployment (Vercel)

### Step 1: Setup Vercel Project

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Create project
cd frontend
vercel
```

### Step 2: Environment Variables

In Vercel Dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add:
   ```
   VITE_API_URL=https://your-domain.com/api
   VITE_WEBSOCKET_URL=https://your-domain.com
   ```

### Step 3: Auto-Deploy on Git Push

1. In Vercel Dashboard → **Git** → **Connect Git**
2. Select your repository
3. Configure:
   - **Production Branch**: `main`
   - **Framework**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

---

## 🔄 GitHub Webhooks for Jenkins

### Step 1: Create Webhook

On GitHub:

1. Go to Repository → **Settings** → **Webhooks**
2. Click **Add webhook**
3. Configure:
   ```
   Payload URL: http://your-jenkins-ip:8080/github-webhook/
   Content type: application/json
   Events: Push events
   Active: ✓ Checked
   ```

### Step 2: Configure Jenkins Job

1. Go to Jenkins Job → **Configure**
2. Under **Build Triggers**, check: **GitHub hook trigger for GITScm polling**
3. Save

Now Jenkins will automatically trigger when you push to `main` branch!

---

## 📊 Monitoring & Logging

### Step 1: View Container Logs

```bash
# SSH to server
ssh root@your-server-ip

# View all logs
cd /opt/apps/restaurant-booking/backend
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f n8n
docker-compose logs -f db
```

### Step 2: Health Check Script

Create `health-check.sh`:

```bash
#!/bin/bash

# Check Backend
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health)
echo "Backend: $BACKEND_STATUS"

# Check N8N
N8N_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5678)
echo "N8N: $N8N_STATUS"

# Check Database
DB_STATUS=$(docker-compose exec -T db pg_isready -h localhost)
echo "Database: $DB_STATUS"

# Check Nginx
NGINX_STATUS=$(systemctl is-active nginx)
echo "Nginx: $NGINX_STATUS"
```

Run with cron:

```bash
# Every 5 minutes
*/5 * * * * /opt/apps/restaurant-booking/health-check.sh >> /opt/apps/restaurant-booking/logs/health.log
```

---

## 🚨 Troubleshooting

### Issue 1: Jenkins can't SSH to server

```bash
# Generate SSH key on Jenkins server (if not exists)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Copy to target server
ssh-copy-id -i ~/.ssh/id_rsa root@your-server-ip

# Test
ssh -i ~/.ssh/id_rsa root@your-server-ip 'echo Connection works'
```

### Issue 2: Docker permission denied

```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Issue 3: Port conflicts

```bash
# Find process using port
lsof -i :8001
lsof -i :5678

# Kill if needed
kill -9 <PID>
```

---

## ✅ Complete Deployment Checklist

- [ ] Server provisioned (Ubuntu 22.04)
- [ ] Docker & Docker Compose installed
- [ ] Jenkins server setup
- [ ] Jenkins plugins installed
- [ ] SSH credentials configured
- [ ] Git credentials configured
- [ ] Jenkinsfile created/configured
- [ ] GitHub webhooks configured
- [ ] Production `.env` created
- [ ] `docker-compose.prod.yml` configured
- [ ] Nginx reverse proxy setup
- [ ] SSL certificate installed
- [ ] Vercel frontend configured
- [ ] Health check script deployed
- [ ] Monitoring setup
- [ ] First deployment tested
- [ ] Automated backups configured

---

## 🎯 Deployment Process Summary

```
1. Developer pushes code to main branch
   ↓
2. GitHub sends webhook to Jenkins
   ↓
3. Jenkins pulls latest code
   ↓
4. Jenkins builds Docker images
   ↓
5. Jenkins runs tests
   ↓
6. If tests pass, deploys to server
   ↓
7. Server runs migrations, restarts containers
   ↓
8. Health checks verify deployment
   ↓
9. Frontend auto-deploys to Vercel
   ↓
10. ✅ Deployment complete!
```

---

## 📞 Quick Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Scale replicas
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

---

## 📚 Additional Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Docker Compose Production](https://docs.docker.com/compose/production/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt with Certbot](https://certbot.eff.org/)
- [Vercel Deployment](https://vercel.com/docs)
