# ⚡ CLScanner • Craigslist Tech Flip Radar

> Automated Craigslist scanner designed to hunt under-\$250 computer hardware, gaming rigs, GPUs, and Apple laptops to flip for maximum profit. Features a sleek web dashboard, automatic flip evaluation, and instant email notifications. Tailor-made to run 24/7 on an Oracle Cloud Always Free server.

![CLScanner Banner](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Alpine.js%20%7C%20TailwindCSS-blue)
![Docker](https://img.shields.io/badge/Docker-Multi--Arch%20(AMD64%20%2F%20ARM64)-emerald)
![Free Cloud Ready](https://img.shields.io/badge/Oracle%20Cloud-Always%20Free%20Ready-orange)

---

## ✨ Features

- 🎯 **Pre-Configured Computer Flipping Benchmarks**:
  - Automatically identifies underpriced **GPUs** (RTX 4060, 3080, 3070, 3060 Ti, 2080 Ti, RX 6800, RX 6700 XT, etc.).
  - Flags underpriced **Gaming Desktops / PC Towers** under \$250.
  - Detects **Apple Silicon MacBooks** (M1 / M2 Air & Pro) under \$250.
  - Monitors high-end **CPUs / Motherboard combos** (Ryzen 7 5800X3D, Ryzen 7800X3D, i7-12700K, i7-13700K).
- 🧠 **Smart Deal Scoring & Margin Estimator**:
  - Calculates estimated market resale value on eBay / Facebook Marketplace.
  - Displays instant flip profit estimates (e.g. `+$120 Profit (55% Margin)`).
  - Categorizes deals:
    - 🔥🔥🔥 **INSANE FLIP** (+\$100 profit or 45%+ margin)
    - 🔥 **GREAT DEAL** (+\$50 profit)
    - 👍 **GOOD PROFIT** (+\$25 profit)
- 🚫 **Negative Keyword & Anti-Scam Filter**:
  - Automatically filters out listings mentioning *"broken"*, *"for parts"*, *"parts only"*, *"bent pins"*, *"icloud locked"*, *"untested"*, *"read description"*, etc.
- 📬 **Instant Email Alerts**:
  - Sends high-conversion, responsive HTML emails with photos, buy price vs resale price, location, and one-click direct links.
  - Includes a direct **"Verify eBay Sold Comps"** button so you can verify live market pricing in 1 click before buying.
  - Built-in deduplication prevents repeated emails for the same listing.
- 💻 **Sleek Web Dashboard**:
  - Real-time dark mode interface powered by Tailwind CSS & Alpine.js.
  - Instant filters (by profit level, status, category, search keywords).
  - Quick actions: Star, Mark as Contacted, Archive / Dismiss.
  - Manual **"Scan Now"** button with live progress indicator.
  - In-app target editor (add/remove cities and categories).
- ☁️ **Lightweight & Free Cloud Ready**:
  - Memory footprint is **< 75MB RAM**, making it run effortlessly on Oracle Cloud's Always Free tier (E2.1 Micro or Ampere A1 ARM64).
  - Zero heavy database required: uses high-speed embedded SQLite with WAL mode.

---

## 🚀 Quickstart (Local Development)

### 1. Clone & Install
```bash
git clone https://github.com/your-username/clscanner.git
cd clscanner

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser to: **`http://localhost:8000`**

---

## ☁️ 24/7 Deployment on Oracle Cloud Always Free

Oracle Cloud offers lifetime free servers (1GB RAM AMD Micro or 24GB RAM Ampere A1 ARM64) that will never charge you.

Follow our detailed step-by-step guide:
👉 **[Read ORACLE_CLOUD_SETUP.md](file:///c:/Users/timme/Documents/GitHub/clscanner/ORACLE_CLOUD_SETUP.md)**

### 1-Command Deploy Script:
Once connected to your Ubuntu VM:
```bash
git clone https://github.com/your-username/clscanner.git
cd clscanner
chmod +x deploy.sh
./deploy.sh
```

---

## ⚙️ Configuration

All configuration can be managed directly through the **Email Alerts & Config** tab in the web dashboard:

| Setting | Default | Description |
|---|---|---|
| `scan_interval_minutes` | `15` | Minutes between automatic background Craigslist scans |
| `max_price_global` | `$250.00` | Upper price limit for items |
| `smtp_host` | `smtp.gmail.com` | SMTP Server (Gmail, Outlook, Yahoo, etc.) |
| `smtp_port` | `587` | Port (587 with STARTTLS or 465 with SSL) |
| `notify_email` | `""` | Recipient email address for deal alerts |

---

## 📁 Project Structure

```
clscanner/
├── app/
│   ├── config.py             # Settings, defaults & paths
│   ├── database.py           # SQLite manager (deals, targets, rules, logs)
│   ├── scraper.py            # Craigslist scraper (JSON-LD + static HTML)
│   ├── deal_analyzer.py      # Resale valuation, profit calculator & scoring
│   ├── notifier.py           # HTML email alert generator & SMTP client
│   ├── scheduler.py          # Background scan scheduler thread
│   └── main.py               # FastAPI application & REST APIs
├── static/                   # Static assets
├── templates/
│   └── index.html            # Web dashboard (Tailwind CSS + Alpine.js)
├── Dockerfile                # Multi-arch lightweight container
├── docker-compose.yml        # Docker compose service definition
├── deploy.sh                 # 1-command installer script for Ubuntu
├── ORACLE_CLOUD_SETUP.md     # Step-by-step Oracle Cloud guide
└── requirements.txt          # Python dependencies
```

---

## 📜 License
MIT License. Built for tech enthusiasts, hardware flippers, and PC builders.
