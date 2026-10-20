import requests
import re
import json
import hashlib
import time
import random
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("clscanner.scraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

def make_listing_id(url: str, title: str) -> str:
    """Generates a stable unique hash ID for the listing."""
    # Look for posting ID in URL first (e.g., /t6FUcijwJjWvzt3CBUhGpa or 7748291823.html)
    match = re.search(r'/([0-9a-zA-Z_-]+)(?:\.html)?$', url.rstrip('/'))
    if match and len(match.group(1)) > 6:
        return f"cl_{match.group(1)}"
    # Fallback to md5 hash of URL
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:16]

def fetch_craigslist_search(city: str, category: str, query: str, max_price: float = 250.0) -> List[Dict[str, Any]]:
    """
    Scrapes Craigslist search results for the given query and price ceiling.
    Combines embedded JSON-LD metadata (images, geo, exact price) with HTML cards.
    """
    city_clean = city.strip().lower()
    cat_clean = category.strip()
    query_clean = query.strip()
    
    # Construct search URL
    base_url = f"https://{city_clean}.craigslist.org/search/{cat_clean}"
    params = {
        "query": query_clean,
        "max_price": int(max_price) if max_price.is_integer() else max_price,
    }
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    }
    
    try:
        resp = requests.get(base_url, params=params, headers=headers, timeout=12)
        if resp.status_code != 200:
            logger.warning(f"Craigslist responded with HTTP {resp.status_code} for {city_clean} - {query_clean}")
            return []
            
        html = resp.text
        
        # 1. Parse JSON-LD Items
        json_items = []
        script_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
        for sm in script_matches:
            try:
                data = json.loads(sm.strip())
                if data.get("@type") == "ItemList" and "itemListElement" in data:
                    for elem in data["itemListElement"]:
                        it = elem.get("item", {})
                        json_items.append(it)
            except Exception:
                continue
                
        # 2. Parse HTML Static Result Cards
        static_matches = re.findall(r'<li class="cl-static-search-result"[^>]*>(.*?)</li>', html, re.DOTALL)
        html_items = []
        for sm in static_matches:
            href_m = re.search(r'href="([^"]+)"', sm)
            title_m = re.search(r'<div class="title">([^<]+)</div>', sm)
            price_m = re.search(r'<div class="price">([^<]+)</div>', sm)
            loc_m = re.search(r'<div class="location">([^<]+)</div>', sm)
            
            raw_price_str = price_m.group(1).strip() if price_m else "0"
            clean_price = re.sub(r'[^\d.]', '', raw_price_str)
            price_val = float(clean_price) if clean_price else 0.0
            
            html_items.append({
                "url": href_m.group(1).strip() if href_m else "",
                "title": title_m.group(1).strip() if title_m else "",
                "price": price_val,
                "location": loc_m.group(1).strip() if loc_m else ""
            })
            
        # 3. Merge JSON-LD with HTML Cards
        results: List[Dict[str, Any]] = []
        count = max(len(json_items), len(html_items))
        
        for i in range(count):
            j_it = json_items[i] if i < len(json_items) else {}
            h_it = html_items[i] if i < len(html_items) else {}
            
            # URL
            url = h_it.get("url") or j_it.get("url", "")
            if not url:
                continue
                
            # If URL is relative, prepend domain
            if url.startswith("/"):
                url = f"https://{city_clean}.craigslist.org{url}"
                
            # Title
            title = j_it.get("name") or h_it.get("title") or ""
            if not title:
                continue
                
            # Price
            price = 0.0
            if "offers" in j_it and isinstance(j_it["offers"], dict):
                p_str = j_it["offers"].get("price", 0)
                try:
                    price = float(p_str)
                except (ValueError, TypeError):
                    price = h_it.get("price", 0.0)
            else:
                price = h_it.get("price", 0.0)
                
            # Image URL
            image_url = ""
            images = j_it.get("image", [])
            if images and isinstance(images, list):
                image_url = images[0]
            elif isinstance(images, str):
                image_url = images
                
            # Location
            location = h_it.get("location", "")
            if not location and "offers" in j_it and "availableAtOrFrom" in j_it["offers"]:
                addr = j_it["offers"]["availableAtOrFrom"].get("address", {})
                location = addr.get("addressLocality", "")
                
            item_id = make_listing_id(url, title)
            
            results.append({
                "id": item_id,
                "title": title,
                "price": price,
                "url": url,
                "image_url": image_url,
                "location": location,
                "city": city_clean,
                "category": cat_clean
            })
            
        logger.info(f"Scraped {len(results)} items for {city_clean} query='{query_clean}'")
        return results
        
    except Exception as e:
        logger.error(f"Error scraping Craigslist for {city_clean} - {query_clean}: {e}")
        return []
