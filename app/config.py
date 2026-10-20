import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "clscanner.db"

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Default Scraping Parameters
DEFAULT_MAX_PRICE = 250.0
DEFAULT_SCAN_INTERVAL_MINUTES = 15

# Default Negative Keywords to filter out broken / scams
DEFAULT_NEGATIVE_KEYWORDS = [
    "broken",
    "for parts",
    "parts only",
    "not working",
    "does not turn on",
    "doesn't turn on",
    "no power",
    "bent pins",
    "damaged screen",
    "cracked screen",
    "icloud locked",
    "bios locked",
    "water damage",
    "bad port",
    "untested sold as is",
    "spares or repair",
    "read description",
    "read ad",
    "box only",
    "empty box"
]

# Preloaded Flip Target Rules (Computer parts & systems under $250 with high flip value)
DEFAULT_FLIP_RULES = [
    # --- GPUs ---
    {
        "keyword": "rtx 4060",
        "category": "GPU",
        "max_buy_price": 250.0,
        "est_resale_value": 310.0,
        "min_profit": 50.0,
        "notes": "Nvidia RTX 4060 8GB"
    },
    {
        "keyword": "rtx 3080",
        "category": "GPU",
        "max_buy_price": 250.0,
        "est_resale_value": 380.0,
        "min_profit": 80.0,
        "notes": "RTX 3080 10GB/12GB - Huge flip profit"
    },
    {
        "keyword": "rtx 3070",
        "category": "GPU",
        "max_buy_price": 240.0,
        "est_resale_value": 300.0,
        "min_profit": 50.0,
        "notes": "RTX 3070 / 3070 Ti"
    },
    {
        "keyword": "rtx 3060 ti",
        "category": "GPU",
        "max_buy_price": 210.0,
        "est_resale_value": 260.0,
        "min_profit": 40.0,
        "notes": "RTX 3060 Ti 8GB"
    },
    {
        "keyword": "rtx 3060",
        "category": "GPU",
        "max_buy_price": 180.0,
        "est_resale_value": 230.0,
        "min_profit": 40.0,
        "notes": "RTX 3060 12GB"
    },
    {
        "keyword": "rtx 2080 ti",
        "category": "GPU",
        "max_buy_price": 240.0,
        "est_resale_value": 320.0,
        "min_profit": 60.0,
        "notes": "RTX 2080 Ti 11GB - Strong resale"
    },
    {
        "keyword": "rtx 2080 super",
        "category": "GPU",
        "max_buy_price": 190.0,
        "est_resale_value": 240.0,
        "min_profit": 40.0,
        "notes": "RTX 2080 Super"
    },
    {
        "keyword": "rtx 2070 super",
        "category": "GPU",
        "max_buy_price": 150.0,
        "est_resale_value": 190.0,
        "min_profit": 35.0,
        "notes": "RTX 2070 Super"
    },
    {
        "keyword": "rx 6800",
        "category": "GPU",
        "max_buy_price": 250.0,
        "est_resale_value": 340.0,
        "min_profit": 70.0,
        "notes": "AMD Radeon RX 6800 / 6800 XT 16GB"
    },
    {
        "keyword": "rx 6700 xt",
        "category": "GPU",
        "max_buy_price": 210.0,
        "est_resale_value": 260.0,
        "min_profit": 45.0,
        "notes": "AMD Radeon RX 6700 XT 12GB"
    },
    {
        "keyword": "gtx 1080 ti",
        "category": "GPU",
        "max_buy_price": 130.0,
        "est_resale_value": 175.0,
        "min_profit": 35.0,
        "notes": "GTX 1080 Ti 11GB"
    },
    # --- Gaming PCs & Desktops ---
    {
        "keyword": "gaming pc",
        "category": "System",
        "max_buy_price": 250.0,
        "est_resale_value": 380.0,
        "min_profit": 70.0,
        "notes": "Complete gaming desktop setup"
    },
    {
        "keyword": "gaming desktop",
        "category": "System",
        "max_buy_price": 250.0,
        "est_resale_value": 360.0,
        "min_profit": 60.0,
        "notes": "Desktop gaming tower"
    },
    # --- Laptops ---
    {
        "keyword": "macbook air m1",
        "category": "Laptop",
        "max_buy_price": 250.0,
        "est_resale_value": 430.0,
        "min_profit": 100.0,
        "notes": "Apple Silicon M1 Air"
    },
    {
        "keyword": "macbook pro m1",
        "category": "Laptop",
        "max_buy_price": 250.0,
        "est_resale_value": 500.0,
        "min_profit": 150.0,
        "notes": "Apple Silicon M1 Pro"
    },
    {
        "keyword": "gaming laptop",
        "category": "Laptop",
        "max_buy_price": 250.0,
        "est_resale_value": 380.0,
        "min_profit": 70.0,
        "notes": "Gaming laptop (Legion, ROG, TUF, etc.)"
    },
    # --- CPUs & Mobo Combos ---
    {
        "keyword": "ryzen 7 5800x3d",
        "category": "CPU",
        "max_buy_price": 180.0,
        "est_resale_value": 260.0,
        "min_profit": 50.0,
        "notes": "Top gaming AM4 CPU"
    },
    {
        "keyword": "ryzen 7 7800x3d",
        "category": "CPU",
        "max_buy_price": 250.0,
        "est_resale_value": 350.0,
        "min_profit": 80.0,
        "notes": "Top gaming AM5 CPU"
    },
    {
        "keyword": "i7-13700k",
        "category": "CPU",
        "max_buy_price": 220.0,
        "est_resale_value": 290.0,
        "min_profit": 50.0,
        "notes": "Intel 13th gen i7"
    },
    {
        "keyword": "i7-12700k",
        "category": "CPU",
        "max_buy_price": 160.0,
        "est_resale_value": 210.0,
        "min_profit": 40.0,
        "notes": "Intel 12th gen i7"
    }
]

# Default Search Targets
DEFAULT_SEARCH_TARGETS = [
    {"city": "losangeles", "category": "sop", "query": "rtx", "max_price": 250.0},
    {"city": "losangeles", "category": "sop", "query": "gtx", "max_price": 250.0},
    {"city": "losangeles", "category": "sop", "query": "rx", "max_price": 250.0},
    {"city": "losangeles", "category": "sys", "query": "gaming pc", "max_price": 250.0},
    {"city": "losangeles", "category": "syp", "query": "gaming laptop", "max_price": 250.0},
    {"city": "losangeles", "category": "syp", "query": "macbook m1", "max_price": 250.0},
    {"city": "losangeles", "category": "sop", "query": "ryzen", "max_price": 250.0},
]
