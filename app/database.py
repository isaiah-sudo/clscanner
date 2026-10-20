import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import (
    DB_PATH,
    DEFAULT_MAX_PRICE,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_NEGATIVE_KEYWORDS,
    DEFAULT_FLIP_RULES,
    DEFAULT_SEARCH_TARGETS
)

logger = logging.getLogger("clscanner.db")

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds default values if newly created."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # 2. Search targets table (cities, queries, categories)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'sop',
                query TEXT NOT NULL,
                max_price REAL NOT NULL DEFAULT 250.0,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_scanned TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Flip rules table (benchmarks for flipping)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flip_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                max_buy_price REAL NOT NULL,
                est_resale_value REAL NOT NULL,
                min_profit REAL NOT NULL DEFAULT 30.0,
                notes TEXT DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Deals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                url TEXT NOT NULL,
                image_url TEXT,
                location TEXT,
                city TEXT,
                category TEXT,
                matched_rule TEXT,
                est_resale_value REAL,
                est_profit REAL,
                profit_margin REAL,
                deal_score INTEGER DEFAULT 1,
                status TEXT DEFAULT 'new',
                notified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. Scan activity logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                city TEXT,
                query TEXT,
                items_found INTEGER DEFAULT 0,
                deals_detected INTEGER DEFAULT 0,
                status_message TEXT
            )
        """)
        
        conn.commit()
        
        # Seed default settings
        default_settings = {
            "smtp_enabled": "false",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": "587",
            "smtp_user": "",
            "smtp_pass": "",
            "smtp_use_tls": "true",
            "notify_email": "",
            "scan_interval_minutes": str(DEFAULT_SCAN_INTERVAL_MINUTES),
            "max_price_global": str(DEFAULT_MAX_PRICE),
            "min_profit_threshold": "30.0",
            "negative_keywords": json.dumps(DEFAULT_NEGATIVE_KEYWORDS),
            "last_scan_time": "",
            "scanner_running": "false"
        }
        
        for k, v in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            
        # Seed default search targets if empty
        cursor.execute("SELECT COUNT(*) FROM search_targets")
        if cursor.fetchone()[0] == 0:
            for target in DEFAULT_SEARCH_TARGETS:
                cursor.execute("""
                    INSERT INTO search_targets (city, category, query, max_price, enabled)
                    VALUES (?, ?, ?, ?, 1)
                """, (target["city"], target["category"], target["query"], target["max_price"]))
                
        # Seed default flip rules if empty
        cursor.execute("SELECT COUNT(*) FROM flip_rules")
        if cursor.fetchone()[0] == 0:
            for rule in DEFAULT_FLIP_RULES:
                cursor.execute("""
                    INSERT INTO flip_rules (keyword, category, max_buy_price, est_resale_value, min_profit, notes, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (
                    rule["keyword"],
                    rule["category"],
                    rule["max_buy_price"],
                    rule["est_resale_value"],
                    rule["min_profit"],
                    rule.get("notes", "")
                ))
                
        conn.commit()

# --- Settings Helpers ---

def get_all_settings() -> Dict[str, str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        settings = {row["key"]: row["value"] for row in rows}
        if "negative_keywords" in settings:
            try:
                settings["negative_keywords_list"] = json.loads(settings["negative_keywords"])
            except Exception:
                settings["negative_keywords_list"] = DEFAULT_NEGATIVE_KEYWORDS
        return settings

def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def update_settings(updates: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        for k, v in updates.items():
            if isinstance(v, (list, dict)):
                v = json.dumps(v)
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (str(k), str(v)))
        conn.commit()

# --- Deals Helpers ---

def insert_deal(deal_data: Dict[str, Any]) -> bool:
    """Inserts a new deal if not already in DB. Returns True if newly inserted."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM deals WHERE id = ?", (deal_data["id"],))
        if cursor.fetchone():
            return False  # Already seen
        
        cursor.execute("""
            INSERT INTO deals (
                id, title, price, url, image_url, location, city, category,
                matched_rule, est_resale_value, est_profit, profit_margin,
                deal_score, status, notified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            deal_data["id"],
            deal_data["title"],
            deal_data["price"],
            deal_data["url"],
            deal_data.get("image_url", ""),
            deal_data.get("location", ""),
            deal_data.get("city", ""),
            deal_data.get("category", ""),
            deal_data.get("matched_rule", ""),
            deal_data.get("est_resale_value", 0.0),
            deal_data.get("est_profit", 0.0),
            deal_data.get("profit_margin", 0.0),
            deal_data.get("deal_score", 1),
        ))
        conn.commit()
        return True

def mark_deal_notified(deal_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE deals SET notified = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (deal_id,))
        conn.commit()

def update_deal_status(deal_id: str, status: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE deals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, deal_id))
        conn.commit()

def delete_deal(deal_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
        conn.commit()

def get_deals(
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM deals WHERE 1=1"
        params = []
        
        if status and status != "all":
            query += " AND status = ?"
            params.append(status)
        elif not status:
            # By default exclude archived
            query += " AND status != 'archived'"
            
        if min_score:
            query += " AND deal_score >= ?"
            params.append(min_score)
            
        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
            
        if search:
            query += " AND (title LIKE ? OR location LIKE ? OR matched_rule LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
            
        query += " ORDER BY deal_score DESC, est_profit DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM deals WHERE status != 'archived'")
        total_active_deals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deals WHERE deal_score = 3 AND status != 'archived'")
        insane_deals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deals WHERE status = 'starred'")
        starred_deals = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(est_profit) FROM deals WHERE status != 'archived' AND est_profit > 0")
        avg_profit_row = cursor.fetchone()[0]
        avg_profit = round(avg_profit_row or 0.0, 2)
        
        cursor.execute("SELECT MAX(est_profit) FROM deals WHERE status != 'archived'")
        max_profit_row = cursor.fetchone()[0]
        max_profit = round(max_profit_row or 0.0, 2)
        
        return {
            "total_active_deals": total_active_deals,
            "insane_deals": insane_deals,
            "starred_deals": starred_deals,
            "avg_profit": avg_profit,
            "max_profit": max_profit
        }

# --- Search Targets Helpers ---

def get_search_targets() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM search_targets ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def add_search_target(city: str, category: str, query: str, max_price: float) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_targets (city, category, query, max_price, enabled)
            VALUES (?, ?, ?, ?, 1)
        """, (city.strip().lower(), category.strip(), query.strip(), max_price))
        conn.commit()
        return cursor.lastrowid

def toggle_search_target(target_id: int, enabled: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE search_targets SET enabled = ? WHERE id = ?", (1 if enabled else 0, target_id))
        conn.commit()

def delete_search_target(target_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM search_targets WHERE id = ?", (target_id,))
        conn.commit()

# --- Flip Rules Helpers ---

def get_flip_rules() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flip_rules ORDER BY category ASC, keyword ASC")
        return [dict(row) for row in cursor.fetchall()]

def add_flip_rule(keyword: str, category: str, max_buy_price: float, est_resale_value: float, min_profit: float, notes: str = "") -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO flip_rules (keyword, category, max_buy_price, est_resale_value, min_profit, notes, enabled)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (keyword.strip().lower(), category.strip(), max_buy_price, est_resale_value, min_profit, notes.strip()))
        conn.commit()
        return cursor.lastrowid

def update_flip_rule(rule_id: int, max_buy_price: float, est_resale_value: float, min_profit: float, notes: str, enabled: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE flip_rules
            SET max_buy_price = ?, est_resale_value = ?, min_profit = ?, notes = ?, enabled = ?
            WHERE id = ?
        """, (max_buy_price, est_resale_value, min_profit, notes, 1 if enabled else 0, rule_id))
        conn.commit()

def toggle_flip_rule(rule_id: int, enabled: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE flip_rules SET enabled = ? WHERE id = ?", (1 if enabled else 0, rule_id))
        conn.commit()

def delete_flip_rule(rule_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM flip_rules WHERE id = ?", (rule_id,))
        conn.commit()

# --- Logging Helpers ---

def log_scan_event(city: str, query: str, items_found: int, deals_detected: int, status_message: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scan_logs (city, query, items_found, deals_detected, status_message)
            VALUES (?, ?, ?, ?, ?)
        """, (city, query, items_found, deals_detected, status_message))
        # Keep only the last 500 logs to prevent unbounded DB growth
        cursor.execute("""
            DELETE FROM scan_logs WHERE id NOT IN (
                SELECT id FROM scan_logs ORDER BY id DESC LIMIT 500
            )
        """)
        conn.commit()

def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scan_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
