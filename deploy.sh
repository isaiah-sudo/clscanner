#!/usr/bin/env bash
# ==============================================================================
# CLScanner - 1-Command Automated Deploy Script for Oracle Cloud Always Free VM
# Works on Ubuntu 20.04, 22.04, and 24.04 (both AMD64 and ARM64 Ampere A1)
# ==============================================================================

set -e

echo "=========================================="
echo "⚡ Deploying CLScanner on Oracle Cloud VM"
echo "=========================================="

# 1. Update OS packages
echo "[1/5] Updating package repositories..."
sudo apt-get update -y

# 2. Install Docker & Docker Compose if not already installed
if ! command -v docker &> /dev/null; then
    echo "[2/5] Installing Docker..."
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "Docker installed successfully."
else
    echo "[2/5] Docker is already installed."
fi

# 3. Open Oracle Linux / Ubuntu Host Firewall for port 8000
echo "[3/5] Configuring host firewall (iptables/ufw) for port 8000..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp || true
fi

# Oracle Cloud Ubuntu instances have iptables REJECT rules by default
if command -v iptables &> /dev/null; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
    if command -v netfilter-persistent &> /dev/null; then
        sudo netfilter-persistent save || true
    fi
fi

# 4. Create data directory
echo "[4/5] Preparing data volume..."
mkdir -p data

# 5. Build and launch Docker container
echo "[5/5] Building and launching CLScanner container..."
if docker compose version &> /dev/null; then
    docker compose down || true
    docker compose up -d --build
else
    docker-compose down || true
    docker-compose up -d --build
fi

echo "=========================================================="
echo "🎉 CLScanner is successfully running!"
echo ""
echo "Access the dashboard in your web browser at:"
echo "👉 http://$(curl -s ifconfig.me):8000"
echo ""
echo "⚠️  REMINDER FOR ORACLE CLOUD:"
echo "Remember to add an Ingress Rule in your Oracle Cloud Console:"
echo "  - Protocol: TCP"
echo "  - Source CIDR: 0.0.0.0/0"
echo "  - Destination Port: 8000"
echo "=========================================================="
