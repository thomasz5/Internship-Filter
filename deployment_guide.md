# Deployment Options for UW Internship Finder

## Option 1: DigitalOcean Droplet ($4-6/month)

### Setup Steps:
1. **Create Droplet**
   ```bash
   # Choose: Ubuntu 22.04, Basic plan, $4/month
   # Get the IP address after creation
   ```

2. **Connect and Setup**
   ```bash
   ssh root@your-droplet-ip
   
   # Install Python and Git
   apt update && apt install python3 python3-pip git -y
   
   # Clone your project
   git clone https://github.com/yourusername/uw-internship-finder.git
   cd uw-internship-finder
   
   # Install dependencies
   pip3 install -r requirements.txt
   ```

3. **Configure Credentials**
   ```bash
   # Create environment file
   nano .env
   # Add your LinkedIn credentials
   
   # Test the system
   python3 main.py github-only
   ```

4. **Setup Auto-Start**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/internship-finder.service
   ```
   
   Service file content:
   ```ini
   [Unit]
   Description=UW Internship Finder
   After=network.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/uw-internship-finder
   Environment=LINKEDIN_EMAIL=your-email@gmail.com
   Environment=LINKEDIN_PASSWORD=your-password
   ExecStart=/usr/bin/python3 main.py monitor
   Restart=always
   RestartSec=60
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   sudo systemctl enable internship-finder
   sudo systemctl start internship-finder
   sudo systemctl status internship-finder
   ```

## Option 2: GitHub Actions (Free but Risky)

**⚠️ WARNING**: This violates LinkedIn's ToS and GitHub's acceptable use policy. Not recommended.

## Option 3: Raspberry Pi ($35 one-time)

Perfect for running 24/7 at home with minimal power consumption:

1. **Setup Raspberry Pi OS**
2. **Install Python and dependencies**
3. **Run continuously** with minimal power usage
4. **Access remotely** via SSH

## Option 4: AWS EC2 Free Tier

- **t2.micro instance** (free for 12 months)
- **Same setup as DigitalOcean**
- **Auto-scaling options** available

## Option 5: Local with Sleep Prevention

Keep your computer awake:

### macOS:
```bash
# Prevent sleep while plugged in
sudo pmset -c sleep 0

# Create a simple keep-awake script
caffeinate -s python3 main.py monitor
```

### Windows:
```powershell
# Use PowerToys or similar to prevent sleep
# Or run in PowerShell with:
powercfg /change standby-timeout-ac 0
```

## Recommended Approach

**For Students**: 
- **Raspberry Pi** ($35) - Set it and forget it
- **DigitalOcean** ($4/month) - Professional solution

**Pros/Cons**:

| Option | Cost | Reliability | Setup Difficulty |
|--------|------|-------------|-----------------|
| Local Computer | Free | Medium | Easy |
| DigitalOcean | $4/month | High | Medium |
| Raspberry Pi | $35 once | High | Medium |
| AWS Free Tier | Free/12mo | High | Hard |

## Security Considerations

- **Never commit credentials** to version control
- **Use environment variables** or encrypted storage
- **Consider using SSH keys** for server access
- **Regular security updates** on cloud servers 