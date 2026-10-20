import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from app.database import (
    get_search_targets,
    insert_deal,
    log_scan_event,
    update_settings,
    get_all_settings
)
from app.scraper import fetch_craigslist_search
from app.deal_analyzer import analyze_listing
from app.notifier import notify_deal_if_enabled

logger = logging.getLogger("clscanner.scheduler")

class ScanScheduler:
    def __init__(self):
        self._thread: threading.Thread = None
        self._running = False
        self._trigger_event = threading.Event()
        self._is_scanning = False
        
    def start(self):
        """Starts background scanner thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scan scheduler background thread started.")
        
    def stop(self):
        """Stops background scanner thread."""
        self._running = False
        self._trigger_event.set()
        
    def trigger_scan_now(self):
        """Signals the background scanner to run an immediate scan."""
        logger.info("Manual scan triggered.")
        self._trigger_event.set()
        
    def is_currently_scanning(self) -> bool:
        return self._is_scanning

    def run_full_scan(self) -> Dict[str, Any]:
        """Executes a complete scan across all enabled targets."""
        if self._is_scanning:
            return {"status": "busy", "message": "Scan already in progress"}
            
        self._is_scanning = True
        update_settings({"scanner_running": "true"})
        start_time = datetime.now()
        
        targets = get_search_targets()
        enabled_targets = [t for t in targets if t.get("enabled", 1)]
        
        total_items_scraped = 0
        new_deals_found = 0
        
        logger.info(f"Starting scan across {len(enabled_targets)} enabled targets...")
        
        try:
            for target in enabled_targets:
                city = target["city"]
                cat = target["category"]
                query = target["query"]
                max_price = float(target.get("max_price", 250.0))
                
                # Fetch raw items
                items = fetch_craigslist_search(city, cat, query, max_price)
                total_items_scraped += len(items)
                target_deals_count = 0
                
                for it in items:
                    deal = analyze_listing(it)
                    if deal:
                        is_new = insert_deal(deal)
                        if is_new:
                            new_deals_found += 1
                            target_deals_count += 1
                            # Dispatch email alert if configured
                            try:
                                notify_deal_if_enabled(deal)
                            except Exception as ne:
                                logger.error(f"Notification error for deal {deal.get('id')}: {ne}")
                                
                log_scan_event(
                    city=city,
                    query=f"{cat}:{query}",
                    items_found=len(items),
                    deals_detected=target_deals_count,
                    status_message=f"Found {len(items)} items, {target_deals_count} new flip deals"
                )
                
                # Small pause between targets to avoid rate limiting
                time.sleep(1.0)
                
            finish_time = datetime.now()
            duration = (finish_time - start_time).total_seconds()
            summary = (
                f"Scan finished in {duration:.1f}s. "
                f"Scraped {total_items_scraped} items, found {new_deals_found} new deals."
            )
            logger.info(summary)
            
            update_settings({
                "last_scan_time": finish_time.strftime("%Y-%m-%d %H:%M:%S"),
                "scanner_running": "false"
            })
            
            return {
                "status": "success",
                "items_scraped": total_items_scraped,
                "new_deals": new_deals_found,
                "duration_seconds": duration,
                "timestamp": finish_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Error during scan loop: {e}", exc_info=True)
            update_settings({"scanner_running": "false"})
            return {"status": "error", "message": str(e)}
        finally:
            self._is_scanning = False
            update_settings({"scanner_running": "false"})

    def _run_loop(self):
        """Periodic loop that executes scans at the configured interval."""
        # Initial scan shortly after launch (give server 5 seconds to bind)
        time.sleep(5)
        
        while self._running:
            self.run_full_scan()
            
            # Fetch user-configured scan interval (in minutes)
            settings = get_all_settings()
            try:
                interval_minutes = float(settings.get("scan_interval_minutes", 15))
            except ValueError:
                interval_minutes = 15.0
                
            interval_seconds = max(interval_minutes * 60, 60)  # at least 1 min
            
            # Wait for either interval timeout OR manual trigger
            triggered = self._trigger_event.wait(timeout=interval_seconds)
            if triggered:
                self._trigger_event.clear()

scheduler_instance = ScanScheduler()
