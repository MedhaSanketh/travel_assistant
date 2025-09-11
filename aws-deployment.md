# AWS EC2 Deployment Guide - AI Travel Agent

## Quick Start (10 minutes)

### 1. Launch EC2 Instance
```bash
# Instance: Ubuntu 22.04 LTS
# Type: t3.medium (recommended) or t2.micro (free tier)
# Security Group: Allow ports 22, 5000, 80, 443
```

### 2. Connect and Setup
```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y

# Clone your app
git clone https://github.com/yourusername/ai-travel-agent.git
cd ai-travel-agent

# Install dependencies (using project file)
pip3 install -e .
```

### 3. Environment Variables
```bash
# Create environment file
cp .env.example .env
nano .env

# Add your API keys:
GROQ_API_KEY=your_actual_groq_key
AMADEUS_CLIENT_ID=your_amadeus_id
AMADEUS_CLIENT_SECRET=your_amadeus_secret
AMADEUS_ENV=production  # or test
GOOGLE_PLACES_API_KEY=your_google_key
```

### 4. Test Run
```bash
streamlit run app.py --server.address 0.0.0.0
# Visit: http://your-ec2-ip:5000
```

## Production Setup with Domain & SSL

### 5. Install Nginx
```bash
sudo apt install nginx -y
sudo systemctl enable nginx
```

### 6. Configure Domain
```bash
# Point your domain to EC2 IP in DNS settings
# Create nginx config
sudo nano /etc/nginx/sites-available/travel-agent
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/travel-agent /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL Certificate (Free)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
sudo certbot renew --dry-run
```

### 8. Create System Service
```bash
sudo nano /etc/systemd/system/travel-agent.service
```

```ini
[Unit]
Description=AI Travel Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ai-travel-agent
Environment=PATH=/home/ubuntu/.local/bin:/usr/bin
ExecStart=/usr/local/bin/streamlit run app.py --server.address 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable travel-agent
sudo systemctl start travel-agent
sudo systemctl status travel-agent
```

### 9. Security Setup
```bash
# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Secure SSH (optional)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

## Alternative: Docker Deployment

### 10. Docker Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo apt install docker-compose -y

# Logout and login again
exit
```

### 11. Deploy with Docker
```bash
# Create environment file
cp .env.example .env
nano .env  # Add your API keys

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Monitoring & Maintenance

### Check Application
```bash
# View logs
sudo journalctl -u travel-agent -f
docker-compose logs -f  # if using Docker

# Restart service
sudo systemctl restart travel-agent
docker-compose restart  # if using Docker
```

### Update Application
```bash
git pull origin main
pip3 install -r requirements.txt
sudo systemctl restart travel-agent

# Or with Docker:
docker-compose down
docker-compose up -d --build
```

## Estimated Costs
- **t3.medium EC2**: ~$30/month
- **Elastic IP**: $3.65/month (if unused)
- **Domain**: ~$12/year
- **Total**: ~$35/month

Your travel agent will be accessible at `https://yourdomain.com` with professional SSL security!