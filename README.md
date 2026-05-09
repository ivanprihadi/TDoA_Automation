markdown
# 🛰️ TDOA Localization Automation System

Time Difference of Arrival (TDOA) based RF source localization system dengan Python backend dan Web frontend.

## 📋 Features

- **Real-time Recording**: Multi-channel IQ recording dari 3 RPi receivers
- **Signal Processing**: IQ filtering, correlation, TDOA calculation
- **Hyperbola Generation**: 3-pair hyperbola dari TDOA measurements
- **Location Estimation**: Intersection point calculation
- **Heatmap Visualization**: MSE-based probability heatmap
- **Interactive Maps**: Leaflet-based HTML maps dengan Folium
- **Web Dashboard**: Flask-based monitoring & control interface
- **Batch Processing**: Multiple triplet processing automation

## 🏗️ Architecture

Recording (RPi) → Signal Processing → TDOA Calculation
↓
Hyperbola Gen
↓
Intersection
↓
Visualization

bash

## 📦 Requirements

- Python 3.8+
- Raspberry Pi (3x) dengan RTL-SDR dongle
- 2+ GB disk space untuk recorded data

## 🚀 Quick Start

### 1. Installation

```bash  
# Clone repository  
git clone <repo-url>  
cd tdoa_automation_app  

# Create virtual environment  
python -m venv venv  
source venv/bin/activate  # Linux/Mac  
# atau  
venv\Scripts\activate  # Windows  

# Install dependencies  
pip install -r requirements.txt  
2. Configuration
bash
# Copy config template
cp config.json.example config.json

# Edit configuration dengan RPi addresses & coordinates
nano config.json
3. Run Application
bash
# Development
python main.py

# Production (dengan gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 main:app
Akses web interface di: http://localhost:5000

4. Docker (Optional)
bash
# Build image
docker build -t tdoa-app .

# Run container
docker-compose up -d

📊 Usage
Web Interface
Dashboard: View system status dan receiver positions
Processing: Select IQ files dan configure parameters
Results: View generated maps dan TDOA results
Configuration: Manage system settings
API Endpoints
bash
GET  /api/status              - System status
GET  /api/config              - Configuration
GET  /api/receivers           - Receiver list
GET  /api/files               - Available IQ files
POST /api/process             - Process triplet files
POST /api/batch-process       - Batch processing
GET  /api/maps                - Generated maps
🔧 Configuration
Edit config.json untuk:

Receiver GPS coordinates
Sample rate & bandwidth
Heatmap resolution
Output directories
📝 MATLAB Files
Original MATLAB implementation:

matlab/read_file_iq.m - IQ file reading
matlab/filter_iq.m - FIR filtering
matlab/correlate_iq.m - Signal correlation
matlab/evaluation_main.m - Main processing
matlab/create_heatmap.m - Heatmap generation
matlab/run_batch_evaluation.m - Batch processing
🧪 Testing
bash
# Run tests
pytest tests/

# With coverage
pytest --cov=backend tests/
📚 Documentation
SETUP.md - Detailed setup guide
API.md - API documentation
CONFIG.md - Configuration guide
🐛 Troubleshooting
Connection Issues
bash
# Test RPi connectivity
ping <rpi-hostname>
ssh pi@<rpi-hostname>
File Reading Errors
bash
# Check file format
file recorded_data/*.dat
# Should output: data
Recording Not Working
bash
# Check RTL-SDR device
rtl_test -t
📄 License
MIT License - See LICENSE file

👨‍💻 Author
TDOA Development Team

🤝 Contributing
Pull requests welcome! Please follow:

PEP 8 style guide
Add tests for new features
Update documentation
Last Updated: 2024
Version: 1.0.0

yaml

---

## **6️⃣ FILE: `SETUP.md`**
**Lokasi:** `tdoa_automation_app/SETUP.md`

```markdown  
# 🔧 Detailed Setup Guide  

## Prerequisites  

### PC Requirements  
- Python 3.8 or higher  
- 4GB RAM minimum  
- Internet connection  

### Raspberry Pi Requirements (3x)  
- Raspberry Pi 3B+ or 4  
- 32GB microSD card  
- RTL-SDR USB dongle (RTL2832U)  
- SSH enabled  

## Step 1: Raspberry Pi Setup  

### 1.1 Flash OS  
```bash
# Download Raspberry Pi OS Lite
# Use Balena Etcher untuk flash ke microSD

# Default credentials:
# Username: pi
# Password: raspberry
1.2 Initial Configuration
bash
# SSH into RPi
ssh pi@<rpi-hostname>

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git build-essential cmake libusb-dev

# Install RTL-SDR driver
git clone https://github.com/osmocom/rtl-sdr.git
cd rtl-sdr
mkdir build
cd build
cmake ../ -DINSTALL_UDEV_RULES=ON -DDETACH_KERNEL_DRIVER=ON
make
sudo make install
sudo ldconfig

# Test RTL-SDR
rtl_test -t
1.3 Create Data Directory
bash
mkdir -p /home/pi/recorded_data
chmod 755 /home/pi/recorded_data
1.4 Setup SSH Key Authentication (Optional but Recommended)
bash
# On PC: Generate key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/rpi_key

# On PC: Copy key to RPi
ssh-copy-id -i ~/.ssh/rpi_key.pub pi@<rpi-hostname>

# Now connect without password
ssh -i ~/.ssh/rpi_key pi@<rpi-hostname>
Step 2: PC Setup
2.1 Clone Repository
bash
git clone <repo-url>
cd tdoa_automation_app
2.2 Virtual Environment
bash
# Create venv
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
2.3 Install Dependencies
bash
pip install -r requirements.txt
2.4 Configuration
bash
# Copy example config
cp config.json.example config.json

# Edit dengan text editor
nano config.json

# PENTING: Update:
# - receivers[rx1,rx2,rx3].hostname dengan RPi addresses
# - receivers[rx1,rx2,rx3].latitude/longitude dengan actual coordinates
# - transmitter.reference dengan reference TX location
2.5 Create Output Directories
bash
mkdir -p output/maps output/recorded_data output/results logs
Step 3: Network Configuration
3.1 Static IP Assignment (Optional)
bash
# Edit /etc/dhcpcd.conf di setiap RPi
sudo nano /etc/dhcpcd.conf

# Add:
interface eth0
static ip_address=192.168.1.10X/24  # X=1,2,3
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
3.2 Hostname Setup
bash
# Edit /etc/hostname
sudo nano /etc/hostname
# Set: rpi-rx1, rpi-rx2, rpi-rx3

# Restart
sudo reboot
3.3 SSH Configuration
bash
# Edit ~/.ssh/config di PC
Host rpi-rx1
    HostName <rpi-ip-1>
    User pi
    IdentityFile ~/.ssh/rpi_key

Host rpi-rx2
    HostName <rpi-ip-2>
    User pi
    IdentityFile ~/.ssh/rpi_key

Host rpi-rx3
    HostName <rpi-ip-3>
    User pi
    IdentityFile ~/.ssh/rpi_key
Step 4: Testing
4.1 Connectivity Test
bash
# Test each RPi
ssh pi@rpi-rx1 "echo 'Connected to RX1'"
ssh pi@rpi-rx2 "echo 'Connected to RX2'"
ssh pi@rpi-rx3 "echo 'Connected to RX3'"
4.2 RTL-SDR Test
bash
# Test each receiver
ssh pi@rpi-rx1 "rtl_test -t"
4.3 Application Test
bash
# Run Flask app
python main.py

# Open browser
# http://localhost:5000

# Test API
curl http://localhost:5000/api/health
Step 5: Recording Verification
5.1 Manual Recording Test
bash
# SSH ke RPi
ssh pi@rpi-rx1

# Record 10 seconds
rtl_sdr -f 1000000000 -s 2048000 -g 40 /home/pi/recorded_data/test.dat &
sleep 10
killall rtl_sdr

# Check file
ls -lh /home/pi/recorded_data/test.dat
# Should be ~20MB for 10 seconds
5.2 Data Download
bash
# From PC
scp pi@rpi-rx1:/home/pi/recorded_data/test.dat ./recorded_data/1_test.dat
Step 6: Production Deployment
6.1 Using Gunicorn
bash
# Install gunicorn
pip install gunicorn

# Run
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 main:app
6.2 Using Docker
bash
# Build
docker build -t tdoa-app .

# Run
docker run -p 5000:5000 -v $(pwd)/output:/app/output tdoa-app
6.3 Systemd Service (Linux)
bash
# Create service file
sudo nano /etc/systemd/system/tdoa-app.service

[Unit]
Description=TDOA Localization App
After=network.target

[Service]
Type=notify
User=<your-user>
WorkingDirectory=/path/to/tdoa_automation_app
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target

# Enable & start
sudo systemctl enable tdoa-app
sudo systemctl start tdoa-app
Troubleshooting
Issue: Cannot connect to RPi
bash
# Check network
ping <rpi-ip>

# Check SSH
ssh -v pi@<rpi-ip>

# Check firewall
sudo ufw allow 22
Issue: RTL-SDR not detected
bash
# List USB devices
lsusb

# Check permissions
sudo usermod -a -G plugdev pi
Issue: Port 5000 already in use
bash
# Kill process
sudo lsof -i :5000
sudo kill -9 <PID>

# Or use different port
FLASK_PORT=5001 python main.py
Successfully set up! You're ready to go! 🎉

bash

---

## **7️⃣ FILE: `Dockerfile`**
**Lokasi:** `tdoa_automation_app/Dockerfile`

```dockerfile  
# Use Python 3.9 slim image  
FROM python:3.9-slim  

# Set working directory  
WORKDIR /app  

# Install system dependencies  
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*  

# Copy requirements  
COPY requirements.txt .  

# Install Python dependencies  
RUN pip install --no-cache-dir -r requirements.txt  

# Copy application  
COPY . .  

# Create output directories  
RUN mkdir -p output/maps output/recorded_data output/results logs  

# Expose port  
EXPOSE 5000  

# Health check  
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')"  

# Run application  
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "300", "main:app"]  
