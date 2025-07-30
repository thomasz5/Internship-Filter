# AWS Free Tier Deployment Guide for UW Internship Finder

## 🎯 What You Get with AWS Free Tier
- **t2.micro instance** (1 vCPU, 1 GB RAM)
- **750 hours/month** for 12 months (basically 24/7)
- **30 GB EBS storage**
- **750 hours of Elastic Load Balancing**
- **Perfect for your internship finder!**

## 🚀 Step-by-Step Setup

### Step 1: Create AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. **Use your .edu email** for potential student credits
4. **Add payment method** (required but won't charge for free tier)
5. **Verify phone number**

### Step 2: Launch EC2 Instance

1. **Go to EC2 Dashboard**
   - Search "EC2" in AWS Console
   - Click "Launch Instance"

2. **Configure Instance**
   ```
   Name: UW-Internship-Finder
   Application and OS Images: Ubuntu Server 22.04 LTS (Free tier eligible)
   Instance type: t2.micro (Free tier eligible)
   Key pair: Create new key pair
   ```

3. **Create Key Pair** (IMPORTANT!)
   ```
   Key pair name: uw-internship-finder-key
   Key pair type: RSA
   Private key file format: .pem
   ```
   **Download and save the .pem file securely!**

4. **Network Settings**
   ```
   ✅ Allow SSH traffic from: My IP
   ✅ Allow HTTPS traffic from internet
   ✅ Allow HTTP traffic from internet
   ```

5. **Storage**
   ```
   8 GB gp3 (Free tier eligible)
   ```

6. **Click "Launch Instance"**

### Step 3: Connect to Your Instance

1. **Find your instance IP**
   - Go to EC2 Dashboard
   - Find your instance
   - Copy "Public IPv4 address"

2. **Connect via SSH** (macOS/Linux)
   ```bash
   # Make key file secure
   chmod 400 ~/Downloads/uw-internship-finder-key.pem
   
   # Connect to instance
   ssh -i ~/Downloads/uw-internship-finder-key.pem ubuntu@YOUR-INSTANCE-IP
   ```

3. **For Windows users**
   - Use PuTTY or Windows Subsystem for Linux

### Step 4: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip git -y

# Install Chrome (for Selenium)
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
sudo apt update
sudo apt install google-chrome-stable -y

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1)
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Verify installation
python3 --version
google-chrome --version
chromedriver --version
```

### Step 5: Setup Your Project

```bash
# Clone your repository (after you push to GitHub)
git clone https://github.com/YOUR-USERNAME/uw-internship-finder.git
cd uw-internship-finder

# Install Python dependencies
pip3 install -r requirements.txt

# Create environment file
nano .env
```

**Add to .env file:**
```bash
LINKEDIN_EMAIL=your-email@gmail.com
LINKEDIN_PASSWORD=your-password
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Test the System

```bash
# Test GitHub monitoring
python3 main.py github-only

# Test Excel creation
python3 main.py excel

# Test summary
python3 main.py summary
```

### Step 7: Setup Auto-Start Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/uw-internship-finder.service
```

**Service file content:**
```ini
[Unit]
Description=UW Internship Finder
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/uw-internship-finder
Environment=LINKEDIN_EMAIL=your-email@gmail.com
Environment=LINKEDIN_PASSWORD=your-password
Environment=DISPLAY=:99
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1024x768x24 &
ExecStart=/usr/bin/python3 main.py monitor
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

**Install virtual display (for Chrome to run without GUI):**
```bash
sudo apt install xvfb -y
```

**Enable and start service:**
```bash
sudo systemctl enable uw-internship-finder
sudo systemctl start uw-internship-finder
sudo systemctl status uw-internship-finder
```

### Step 8: Setup File Transfer (for Excel files)

Since your Excel files are created on the server, you need to download them:

```bash
# From your local computer, download Excel file
scp -i ~/Downloads/uw-internship-finder-key.pem ubuntu@YOUR-INSTANCE-IP:/home/ubuntu/uw-internship-finder/UW_Internship_Tracker.xlsx ~/Downloads/
```

**Or setup automated sync:**
```bash
# On server, install AWS CLI
sudo apt install awscli -y

# Configure S3 bucket (optional)
aws configure
```

## 📊 Monitoring Your System

### Check Status
```bash
# Check if service is running
sudo systemctl status uw-internship-finder

# View logs
sudo journalctl -u uw-internship-finder -f

# Check application logs
tail -f /home/ubuntu/uw-internship-finder/monitor.log
```

### Manual Operations
```bash
# Stop service
sudo systemctl stop uw-internship-finder

# Run manually for testing
cd /home/ubuntu/uw-internship-finder
python3 main.py run

# Restart service
sudo systemctl start uw-internship-finder
```

## 💰 Cost Management

### Free Tier Limits
- **750 hours/month** t2.micro (24/7 for 31 days = 744 hours)
- **30 GB storage** (your project uses ~1 GB)
- **Free for 12 months**

### After Free Tier
- **t2.micro**: ~$8-10/month
- **Consider t2.nano**: ~$4-5/month (512 MB RAM, still sufficient)

### Cost Optimization
```bash
# Stop instance when not needed
aws ec2 stop-instances --instance-ids i-YOUR-INSTANCE-ID

# Start when needed
aws ec2 start-instances --instance-ids i-YOUR-INSTANCE-ID
```

## 🔒 Security Best Practices

### Instance Security
```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Setup firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### Key Management
- **Never share your .pem file**
- **Store it securely** (not in Downloads folder long-term)
- **Backup your .pem file** (if lost, you can't access instance)

### Monitoring
```bash
# Setup CloudWatch alarms for CPU/memory
# Enable detailed monitoring in EC2 console
```

## 📱 Remote Access Options

### Access Excel Files
1. **SCP/SFTP** - Download files manually
2. **S3 Sync** - Automatic cloud sync
3. **Email notifications** - Send updates via email
4. **Web interface** - Create simple web dashboard

### Code Updates
```bash
# Pull latest changes
cd /home/ubuntu/uw-internship-finder
git pull origin main

# Restart service
sudo systemctl restart uw-internship-finder
```

## 🎯 Troubleshooting

### Common Issues

**Chrome won't start:**
```bash
# Install missing dependencies
sudo apt install -y libnss3-dev libgconf-2-4 libxss1 libappindicator1 fonts-liberation
```

**Service fails to start:**
```bash
# Check logs
sudo journalctl -u uw-internship-finder -n 50

# Run manually to debug
python3 main.py github-only
```

**Out of memory:**
```bash
# Add swap space
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Connection issues:**
```bash
# Check security groups in AWS console
# Ensure SSH (port 22) is allowed from your IP
```

## 🚀 Going Further

### Enhancements
- **Add email notifications** when opportunities found
- **Create web dashboard** for remote viewing
- **Setup automated backups** to S3
- **Add Slack/Discord integration** for alerts
- **Scale to multiple regions** for better reliability

### Monitoring
- **CloudWatch dashboards**
- **SNS alerts** for system issues
- **Cost monitoring** and budgets
- **Performance metrics** and optimization

## 💡 Pro Tips

1. **Elastic IP** - Get static IP address ($0.005/hour when instance running)
2. **Auto-scaling** - Automatically handle traffic spikes
3. **Load balancer** - Add redundancy with multiple instances
4. **RDS database** - Move from SQLite to managed PostgreSQL
5. **Lambda functions** - Run specific tasks serverlessly
6. **CloudFormation** - Infrastructure as code for easy deployment

This setup gives you a professional, always-on internship finder running in the cloud! 🎉 