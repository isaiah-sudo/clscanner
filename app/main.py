import logging
import json
import re
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import BASE_DIR, HOST, PORT, DEBUG
from app.database import (
    init_db,
    get_all_settings,
    update_settings,
    get_deals,
    get_stats,
    update_deal_status,
    delete_deal,
    get_search_targets,
    add_search_target,
    toggle_search_target,
    delete_search_target,
    split_composite_targets,
    get_flip_rules,
    add_flip_rule,
    update_flip_rule,
    toggle_flip_rule,
    delete_flip_rule,
    get_recent_logs
)
from app.scheduler import scheduler_instance
from app.notifier import test_smtp_connection

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("clscanner")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and kick off background scheduler
    logger.info("Initializing SQLite database...")
    init_db()
    logger.info("Starting background scan scheduler...")
    scheduler_instance.start()
    yield
    # Shutdown
    logger.info("Stopping background scheduler...")
    scheduler_instance.stop()

app = FastAPI(title="Craigslist Flip Scanner", version="1.0.0", lifespan=lifespan)

# Mount Static and Templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- Pydantic Request Models ---

class TargetCreateRequest(BaseModel):
    city: str
    category: str = "sop"
    query: str
    max_price: float = 250.0

class TargetToggleRequest(BaseModel):
    enabled: bool

class RuleCreateRequest(BaseModel):
    keyword: str
    category: str = "Component"
    max_buy_price: float
    est_resale_value: float
    min_profit: float = 30.0
    notes: Optional[str] = ""

class RuleUpdateRequest(BaseModel):
    max_buy_price: float
    est_resale_value: float
    min_profit: float
    notes: Optional[str] = ""
    enabled: bool = True

class RuleToggleRequest(BaseModel):
    enabled: bool

class DealStatusRequest(BaseModel):
    status: str

class SettingsUpdateRequest(BaseModel):
    smtp_enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    notify_email: Optional[str] = None
    scan_interval_minutes: Optional[int] = None
    max_price_global: Optional[float] = None
    negative_keywords: Optional[List[str]] = None

class TestEmailRequest(BaseModel):
    to_email: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    smtp_use_tls: bool = True

# --- HTML Web Dashboard ---

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# --- REST APIs ---

# 1. Deals API
@app.get("/api/deals")
def api_get_deals(
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    deals = get_deals(
        status=status,
        min_score=min_score,
        category=category,
        search=search,
        limit=limit,
        offset=offset
    )
    return {"deals": deals, "count": len(deals)}

@app.post("/api/deals/{deal_id}/status")
def api_update_deal_status(deal_id: str, req: DealStatusRequest):
    if req.status not in ["new", "starred", "contacted", "bought", "archived"]:
        raise HTTPException(status_code=400, detail="Invalid deal status")
    update_deal_status(deal_id, req.status)
    return {"success": True, "deal_id": deal_id, "status": req.status}

@app.delete("/api/deals/{deal_id}")
def api_delete_deal(deal_id: str):
    delete_deal(deal_id)
    return {"success": True, "deal_id": deal_id}

@app.get("/api/stats")
def api_get_stats():
    stats = get_stats()
    settings = get_all_settings()
    stats["last_scan_time"] = settings.get("last_scan_time", "Never")
    stats["is_scanning"] = scheduler_instance.is_currently_scanning()
    stats["scan_interval_minutes"] = settings.get("scan_interval_minutes", "15")
    stats["smtp_enabled"] = settings.get("smtp_enabled", "false").lower() == "true"
    return stats

# 2. Search Targets API
@app.get("/api/targets")
def api_get_targets():
    return {"targets": get_search_targets()}

@app.post("/api/targets")
def api_add_target(req: TargetCreateRequest):
    # Support multiple cities if comma-separated
    cities = [c.strip().lower() for c in re.split(r'[,;\n]+', req.city) if c.strip()]
    if not cities:
        cities = [req.city.strip().lower()]
        
    all_created_ids = []
    for city in cities:
        ids = add_search_target(city, req.category, req.query, req.max_price)
        all_created_ids.extend(ids)
        
    return {"success": True, "ids": all_created_ids, "count": len(all_created_ids)}

@app.post("/api/targets/split")
def api_split_targets():
    count = split_composite_targets()
    return {"success": True, "split_count": count}

@app.post("/api/targets/{target_id}/toggle")
def api_toggle_target(target_id: int, req: TargetToggleRequest):
    toggle_search_target(target_id, req.enabled)
    return {"success": True}

@app.delete("/api/targets/{target_id}")
def api_delete_target(target_id: int):
    delete_search_target(target_id)
    return {"success": True}

# 3. Flip Rules API
@app.get("/api/rules")
def api_get_rules():
    return {"rules": get_flip_rules()}

@app.post("/api/rules")
def api_add_rule(req: RuleCreateRequest):
    rule_id = add_flip_rule(
        keyword=req.keyword,
        category=req.category,
        max_buy_price=req.max_buy_price,
        est_resale_value=req.est_resale_value,
        min_profit=req.min_profit,
        notes=req.notes or ""
    )
    return {"success": True, "id": rule_id}

@app.put("/api/rules/{rule_id}")
def api_update_rule(rule_id: int, req: RuleUpdateRequest):
    update_flip_rule(
        rule_id=rule_id,
        max_buy_price=req.max_buy_price,
        est_resale_value=req.est_resale_value,
        min_profit=req.min_profit,
        notes=req.notes or "",
        enabled=req.enabled
    )
    return {"success": True}

@app.post("/api/rules/{rule_id}/toggle")
def api_toggle_rule(rule_id: int, req: RuleToggleRequest):
    toggle_flip_rule(rule_id, req.enabled)
    return {"success": True}

@app.delete("/api/rules/{rule_id}")
def api_delete_rule(rule_id: int):
    delete_flip_rule(rule_id)
    return {"success": True}

# 4. Settings & Scanner Controls
@app.get("/api/settings")
def api_get_settings():
    return get_all_settings()

@app.post("/api/settings")
def api_update_settings(req: SettingsUpdateRequest):
    updates = {}
    if req.smtp_enabled is not None:
        updates["smtp_enabled"] = "true" if req.smtp_enabled else "false"
    if req.smtp_host is not None:
        updates["smtp_host"] = req.smtp_host
    if req.smtp_port is not None:
        updates["smtp_port"] = str(req.smtp_port)
    if req.smtp_user is not None:
        updates["smtp_user"] = req.smtp_user
    if req.smtp_pass is not None:
        updates["smtp_pass"] = req.smtp_pass
    if req.smtp_use_tls is not None:
        updates["smtp_use_tls"] = "true" if req.smtp_use_tls else "false"
    if req.notify_email is not None:
        updates["notify_email"] = req.notify_email
    if req.scan_interval_minutes is not None:
        updates["scan_interval_minutes"] = str(req.scan_interval_minutes)
    if req.max_price_global is not None:
        updates["max_price_global"] = str(req.max_price_global)
    if req.negative_keywords is not None:
        updates["negative_keywords"] = json.dumps(req.negative_keywords)
        
    update_settings(updates)
    return {"success": True, "settings": get_all_settings()}

@app.post("/api/test-email")
def api_test_email(req: TestEmailRequest):
    config = {
        "smtp_host": req.smtp_host,
        "smtp_port": req.smtp_port,
        "smtp_user": req.smtp_user,
        "smtp_pass": req.smtp_pass,
        "smtp_use_tls": req.smtp_use_tls
    }
    success, message = test_smtp_connection(req.to_email, config)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

@app.post("/api/scan-now")
def api_scan_now():
    if scheduler_instance.is_currently_scanning():
        return {"status": "busy", "message": "Scan already in progress."}
    scheduler_instance.trigger_scan_now()
    return {"status": "triggered", "message": "Background scan started!"}

@app.get("/api/scan-status")
def api_scan_status():
    settings = get_all_settings()
    return {
        "is_scanning": scheduler_instance.is_currently_scanning(),
        "last_scan_time": settings.get("last_scan_time", "Never")
    }

@app.get("/api/logs")
def api_get_logs():
    return {"logs": get_recent_logs(limit=50)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
