# ☁️ Deploying CLScanner on Oracle Cloud Always Free

This guide walks you through deploying **CLScanner** onto a completely free, 24/7 cloud server using **Oracle Cloud Always Free Tier**.

---

## 📋 What You Get With Oracle Cloud Always Free
- **Zero Cost Forever**: Oracle provides free compute VMs that never expire.
- **Specs Choice**:
  - **AMD x86**: `VM.Standard.E2.1.Micro` (1 OCPU, 1 GB RAM) — Perfect for CLScanner (CLScanner uses < 80MB RAM).
  - **ARM Ampere A1**: Up to 4 OCPUs and 24 GB RAM (CLScanner's Dockerfile supports ARM64 natively).
- **Static Public IP**: Access your web dashboard from anywhere.

---

## 🚀 Step 1: Create Your Free Compute Instance

1. Log into your [Oracle Cloud Console](https://cloud.oracle.com/).
2. In the navigation menu (top left), click **Compute** → **Instances**.
3. Click **Create Instance**.
4. Configure the instance:
   - **Name**: `clscanner-server`
   - **Image and shape**:
     - Image: **Canonical Ubuntu 22.04** or **24.04** Minimal / Standard
     - Shape: **VM.Standard.E2.1.Micro** (Always Free-eligible) OR **VM.Standard.A1.Flex**
   - **Networking**:
     - Select or create a Virtual Cloud Network (VCN) and public subnet.
     - Ensure **Assign a public IPv4 address** is checked.
   - **Add SSH keys**:
     - Choose **Generate a key pair for me** and download both the **Private Key** and **Public Key**.
5. Click **Create**.
6. Wait 1-2 minutes until the instance state changes to **Running**.
7. Note down the **Public IP Address** (e.g. `129.153.xx.xx`).

---

## 🔓 Step 2: Open Oracle Cloud Firewall (VCN Security List)

> [!IMPORTANT]
> Oracle Cloud blocks all incoming web traffic by default at the virtual cloud router level. You **must** open port `8000` in the Security List, otherwise you will not be able to open the website.

1. In your instance details page, under **Instance Information**, click on your **Virtual Cloud Network (VCN)**.
2. In the left sidebar, click **Security Lists**.
3. Click on the **Default Security List for your VCN**.
4. Under **Ingress Rules**, click **Add Ingress Rules**.
5. Enter the following:
   - **Source Type**: `CIDR`
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: `TCP`
   - **Destination Port Range**: `8000`
   - **Description**: `CLScanner Web Dashboard`
6. Click **Add Ingress Rules**.

---

## 💻 Step 3: Connect to Your VM via SSH

Open PowerShell (Windows) or Terminal (Mac/Linux):

```bash
# Set proper permissions for your private key (Mac/Linux only)
chmod 400 /path/to/ssh-key.key

# Connect to your Oracle VM (default user is 'ubuntu')
ssh -i /path/to/ssh-key.key ubuntu@<YOUR_PUBLIC_IP>
```

---

## ⚡ Step 4: Deploy CLScanner (1-Command Method)

Once logged into your server, run:

```bash
# Clone the repository
git clone https://github.com/your-username/clscanner.git
cd clscanner

# Make the deploy script executable and run it
chmod +x deploy.sh
./deploy.sh
```

The script will automatically:
1. Update Ubuntu packages.
2. Install Docker & Docker Compose if missing.
3. Configure the local `iptables` / `ufw` firewall to allow port 8000.
4. Build the container and start it in the background (`docker compose up -d`).

---

## 🌐 Step 5: Open the Web Dashboard

Open your web browser and navigate to:
```
http://<YOUR_ORACLE_PUBLIC_IP>:8000
```

You will see the **CLScanner Dashboard** live!

---

## 📬 Step 6: Setting Up Email Notifications (Gmail / Outlook)

CLScanner can send instant notifications to your email when a flip-worthy deal under \$250 is found.

### For Gmail:
1. Go to your **Google Account** → **Security**.
2. Turn on **2-Step Verification** (if not already enabled).
3. Search for or navigate to **App passwords** (`https://myaccount.google.com/apppasswords`).
4. Create a new App Password:
   - App name: `CLScanner`
5. Google will generate a 16-character password (e.g., `abcd efgh ijkl mnop`).
6. In the CLScanner Web Dashboard:
   - Go to the **Email Alerts & Config** tab.
   - Toggle **Email Notifications** to **ON**.
   - **Notification Email**: Your personal email where you want to receive alerts.
   - **SMTP Host**: `smtp.gmail.com`
   - **SMTP Port**: `587`
   - **SMTP User**: Your Gmail address.
   - **SMTP Password**: The 16-character Google App Password.
   - Click **Send Test Email** to verify!
   - Click **Save Settings**.

---

## 🛠️ Alternative: Run Directly with Python (Without Docker)

If you prefer running without Docker:

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

cd clscanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service for 24/7 background operation:
sudo nano /etc/systemd/system/clscanner.service
```

Paste the following:

```ini
[Unit]
Description=CLScanner Craigslist Tech Flip Finder
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/clscanner
ExecStart=/home/ubuntu/clscanner/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now clscanner
```

Check status:
```bash
sudo systemctl status clscanner
```

---

## 🔍 Useful Maintenance Commands

```bash
# View live container logs
docker compose logs -f

# Restart scanner
docker compose restart

# Update to latest version
git pull
docker compose up -d --build

# Check SQLite database file
ls -la data/
```
