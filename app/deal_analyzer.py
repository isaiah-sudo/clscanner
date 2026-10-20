import re
from typing import Dict, Any, Optional, List, Tuple
from app.database import get_flip_rules, get_all_settings

def normalize_text(text: str) -> str:
    """Normalizes string for robust regex and keyword matching."""
    if not text:
        return ""
    # Lowercase, replace hyphens and underscores with spaces, collapse spaces
    cleaned = text.lower().replace("-", " ").replace("_", " ").replace("/", " ")
    return " " + " ".join(cleaned.split()) + " "

def contains_negative_keyword(title: str, negative_keywords: List[str]) -> Tuple[bool, str]:
    """Checks if listing title contains disqualifying terms (broken, parts only, etc.)."""
    norm = normalize_text(title)
    for kw in negative_keywords:
        kw_norm = normalize_text(kw).strip()
        if not kw_norm:
            continue
        # Check as whole word or boundary phrase
        pattern = r'\b' + re.escape(kw_norm) + r'\b'
        if re.search(pattern, norm):
            return True, kw
    return False, ""

def match_rule(title: str, price: float, rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Finds the most specific matching flip rule for a given listing.
    Rules are sorted by length of keyword descending so 'rtx 3070 ti' matches before 'rtx 3070'.
    """
    norm = normalize_text(title)
    
    # Sort by keyword length descending (most specific first)
    sorted_rules = sorted(rules, key=lambda r: len(r["keyword"]), reverse=True)
    
    for rule in sorted_rules:
        if not rule.get("enabled", 1):
            continue
            
        kw = rule["keyword"].lower().strip()
        parts = kw.split()
        
        # All words of keyword must appear in the title in sequence or proximity
        matched = True
        for part in parts:
            if not re.search(r'\b' + re.escape(part) + r'\b', norm):
                matched = False
                break
                
        if matched:
            # Check price threshold
            max_buy = float(rule["max_buy_price"])
            if price > max_buy:
                # Exceeds maximum buying price for this flip rule
                continue
                
            est_resale = float(rule["est_resale_value"])
            min_profit = float(rule.get("min_profit", 25.0))
            est_profit = est_resale - price
            
            if est_profit < min_profit:
                continue
                
            margin = (est_profit / est_resale * 100) if est_resale > 0 else 0
            
            # Determine deal score
            if est_profit >= 100 or margin >= 45:
                deal_score = 3  # 🔥🔥🔥 INSANE DEAL
            elif est_profit >= 50 or margin >= 25:
                deal_score = 2  # 🔥 GREAT DEAL
            else:
                deal_score = 1  # 👍 GOOD DEAL
                
            return {
                "matched_rule": rule["keyword"].upper(),
                "category": rule.get("category", "Component"),
                "est_resale_value": est_resale,
                "est_profit": round(est_profit, 2),
                "profit_margin": round(margin, 1),
                "deal_score": deal_score,
                "notes": rule.get("notes", "")
            }
            
    return None

def analyze_listing(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyzes a raw Craigslist scraped item.
    Returns enriched deal dictionary if it qualifies as a good flip, or None if disqualified.
    """
    title = item.get("title", "").strip()
    price = float(item.get("price", 0.0))
    
    # Ignore zero price (often 'free' clickbait or $1 spam) or over $250
    if price < 5.0 or price > 250.0:
        return None
        
    settings = get_all_settings()
    neg_list = settings.get("negative_keywords_list", [])
    
    # 1. Filter out negatives
    has_neg, neg_kw = contains_negative_keyword(title, neg_list)
    if has_neg:
        return None
        
    # 2. Match flip rules
    rules = get_flip_rules()
    evaluation = match_rule(title, price, rules)
    
    # 3. Fallback heuristic: Check for obvious high-value computer keywords under $250
    if not evaluation:
        norm = normalize_text(title)
        
        # Complete gaming PC heuristic under $250
        if "gaming pc" in norm or "gaming desktop" in norm or "gaming computer" in norm:
            est_resale = 360.0
            est_profit = est_resale - price
            if est_profit >= 40.0:
                evaluation = {
                    "matched_rule": "GAMING PC (BUNDLE)",
                    "category": "System",
                    "est_resale_value": est_resale,
                    "est_profit": round(est_profit, 2),
                    "profit_margin": round(est_profit / est_resale * 100, 1),
                    "deal_score": 3 if est_profit >= 100 else 2,
                    "notes": "Full gaming PC build under $250"
                }
        # Apple M1/M2 silicon heuristic
        elif ("macbook" in norm and ("m1" in norm or "m2" in norm or "m3" in norm)):
            est_resale = 450.0
            est_profit = est_resale - price
            evaluation = {
                "matched_rule": "APPLE SILICON MACBOOK",
                "category": "Laptop",
                "est_resale_value": est_resale,
                "est_profit": round(est_profit, 2),
                "profit_margin": round(est_profit / est_resale * 100, 1),
                "deal_score": 3,
                "notes": "M-series MacBook under $250"
            }
            
    if not evaluation:
        return None
        
    # Build complete deal payload
    deal = {
        "id": item["id"],
        "title": title,
        "price": price,
        "url": item.get("url", ""),
        "image_url": item.get("image_url", ""),
        "location": item.get("location", ""),
        "city": item.get("city", ""),
        "category": evaluation["category"],
        "matched_rule": evaluation["matched_rule"],
        "est_resale_value": evaluation["est_resale_value"],
        "est_profit": evaluation["est_profit"],
        "profit_margin": evaluation["profit_margin"],
        "deal_score": evaluation["deal_score"],
    }
    
    return deal
