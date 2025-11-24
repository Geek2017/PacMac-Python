# Deploying PacMac to AWS Lightsail

## Overview

Since PacMac is a Pygame desktop application, deploying it to AWS Lightsail requires converting it to a web-based game. This guide covers multiple approaches.

---

## Option 1: Pygame WebAssembly (Pygbag) - Recommended

Convert your Pygame game to run in browsers using WebAssembly, then deploy as a static site.

### Step 1: Install Pygbag

```bash
pip install pygbag
```

### Step 2: Prepare Your Code

Modify `main.py` to be async-compatible:

```python
import asyncio
import pygame

# Your existing game code...

async def main():
    # Move all game loop code here
    global running
    while running:
        # Your existing game loop
        await asyncio.sleep(0)  # Allow browser to handle events

    pygame.quit()

# Entry point
asyncio.run(main())
```

### Step 3: Build for Web

```bash
pygbag main.py
```

This creates a `build/web` directory with HTML/JS/WASM files.

### Step 4: Deploy to AWS Lightsail

#### Option A: Static Website Hosting

1. **Create S3 Bucket** (simpler than Lightsail for static sites):
   ```bash
   aws s3 mb s3://pacmac-game
   aws s3 sync build/web s3://pacmac-game --acl public-read
   aws s3 website s3://pacmac-game --index-document index.html
   ```

2. **Access your game**: http://pacmac-game.s3-website-us-east-1.amazonaws.com

#### Option B: Lightsail Static IP + Nginx

1. **Create Lightsail Instance**:
   - Go to AWS Lightsail Console
   - Create instance: OS Only → Ubuntu 22.04 LTS
   - Choose plan: $3.50/month (512 MB RAM)

2. **SSH into instance**:
   ```bash
   ssh ubuntu@YOUR_LIGHTSAIL_IP
   ```

3. **Install Nginx**:
   ```bash
   sudo apt update
   sudo apt install nginx -y
   ```

4. **Upload game files**:
   ```bash
   # On your local machine
   scp -r build/web/* ubuntu@YOUR_LIGHTSAIL_IP:/tmp/pacmac

   # On Lightsail instance
   sudo mv /tmp/pacmac/* /var/www/html/
   sudo systemctl restart nginx
   ```

5. **Configure firewall** (in Lightsail console):
   - Allow HTTP (port 80)
   - Allow HTTPS (port 443) if using SSL

6. **Access**: http://YOUR_LIGHTSAIL_IP

---

## Option 2: Python Web Framework (Flask/Django)

Rewrite the game using JavaScript for the frontend while keeping game logic in Python backend.

### Architecture

```
Frontend (Browser)          Backend (Flask API)
├── HTML Canvas            ├── Game State Manager
├── JavaScript Game Loop   ├── Ghost AI Logic
└── WebSocket Client       └── Score Tracking
```

### Step 1: Create Flask Backend

Create `server.py`:

```python
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state
game_state = {
    'ghosts': [],
    'pellets': [],
    'score': 0,
    'power_mode': False
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('player_move')
def handle_move(data):
    # Process player movement
    # Update game state
    # Emit updated state to client
    emit('game_update', game_state, broadcast=True)

@socketio.on('collect_pellet')
def handle_pellet(data):
    # Update score
    # Check win condition
    emit('score_update', {'score': game_state['score']})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

### Step 2: Create Frontend

Create `templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>PacMac</title>
    <style>
        canvas { border: 1px solid black; }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="420" height="360"></canvas>
    <div>Score: <span id="score">0</span></div>

    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        const socket = io();
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');

        // Game rendering logic
        function render(gameState) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            // Draw game objects
        }

        // Listen for keyboard
        document.addEventListener('keydown', (e) => {
            socket.emit('player_move', {
                key: e.key,
                direction: getDirection(e.key)
            });
        });

        // Receive updates
        socket.on('game_update', (state) => {
            render(state);
        });
    </script>
</body>
</html>
```

### Step 3: Deploy to Lightsail

1. **Create requirements.txt**:
```
flask==2.3.0
flask-socketio==5.3.0
python-socketio==5.9.0
eventlet==0.33.3
```

2. **Create deployment script** `deploy.sh`:
```bash
#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv nginx -y

# Create app directory
sudo mkdir -p /var/www/pacmac
sudo chown -R ubuntu:ubuntu /var/www/pacmac
cd /var/www/pacmac

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/pacmac.service > /dev/null <<EOF
[Unit]
Description=PacMac Game Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/pacmac
Environment="PATH=/var/www/pacmac/venv/bin"
ExecStart=/var/www/pacmac/venv/bin/python server.py

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl start pacmac
sudo systemctl enable pacmac

# Configure Nginx reverse proxy
sudo tee /etc/nginx/sites-available/pacmac > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/pacmac /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "Deployment complete! Access at http://YOUR_LIGHTSAIL_IP"
```

3. **Deploy**:
```bash
# Upload files to Lightsail
scp -r . ubuntu@YOUR_LIGHTSAIL_IP:/tmp/pacmac

# SSH and run deployment
ssh ubuntu@YOUR_LIGHTSAIL_IP
cd /tmp/pacmac
chmod +x deploy.sh
./deploy.sh
```

---

## Option 3: Headless Pygame with VNC (Not Recommended)

Run Pygame with a virtual display - complex and resource-intensive.

### Setup

```bash
# Install X virtual framebuffer
sudo apt install xvfb python3-pygame -y

# Run game with virtual display
xvfb-run -a python3 main.py
```

**Limitations**:
- Users need VNC client to connect
- Poor performance over internet
- Not suitable for multiple concurrent users
- Higher Lightsail plan required ($10+/month)

---

## Cost Estimates

| Option | AWS Service | Monthly Cost |
|--------|-------------|--------------|
| Pygbag + S3 | S3 Static Website | ~$0.50-$2 |
| Pygbag + Lightsail | Lightsail 512MB | $3.50 |
| Flask Backend | Lightsail 1GB | $5.00 |
| With Database | Lightsail 2GB + RDS | $15+ |

---

## Recommended Approach

**Best for PacMac**: **Pygbag + S3 Static Website**

### Why?
- ✅ No server maintenance
- ✅ Lowest cost (~$0.50/month)
- ✅ Auto-scaling
- ✅ Fast global delivery with CloudFront
- ✅ Minimal code changes
- ✅ No Python backend needed

### Quick Start Commands

```bash
# 1. Install pygbag
pip install pygbag

# 2. Build game
pygbag main.py

# 3. Deploy to S3
aws s3 sync build/web s3://your-bucket-name --acl public-read
aws s3 website s3://your-bucket-name --index-document index.html

# 4. Done! Share the URL
echo "http://your-bucket-name.s3-website-us-east-1.amazonaws.com"
```

---

## Troubleshooting

### Pygame WebAssembly Issues

**Error**: `asyncio.run() not supported`
- **Fix**: Use `asyncio.get_event_loop().run_until_complete(main())`

**Error**: `Module not found: pygame`
- **Fix**: Ensure pygame version 2.0+ is installed

### Lightsail Connection Issues

**Cannot connect to instance**:
1. Check Lightsail firewall (Networking tab)
2. Ensure port 80 is open
3. Verify security group settings

**Nginx 502 Bad Gateway**:
```bash
# Check if Flask is running
sudo systemctl status pacmac

# View logs
journalctl -u pacmac -f
```

---

## Advanced: Adding HTTPS

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Performance Optimization

### For Static Deployment
- Enable CloudFront CDN for faster global access
- Compress assets with gzip
- Optimize image sizes

### For Flask Backend
- Use Gunicorn with multiple workers
- Enable Redis for session management
- Implement WebSocket connection pooling

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn --worker-class eventlet -w 4 --bind 0.0.0.0:5000 server:app
```

---

## Monitoring

### Lightsail Built-in Metrics
- CPU utilization
- Network in/out
- Disk I/O

### Application Monitoring
```python
# Add to server.py
from flask import request
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    diff = time.time() - request.start_time
    if diff > 1.0:  # Log slow requests
        print(f"Slow request: {request.path} took {diff:.2f}s")
    return response
```

---

## Next Steps

1. Choose deployment option based on requirements
2. Set up AWS account and Lightsail instance
3. Follow step-by-step guide for chosen option
4. Test thoroughly before sharing
5. Monitor performance and costs

**Questions?** Check AWS Lightsail documentation or Pygame-Web community forums.
