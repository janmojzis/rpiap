#!/usr/bin/env python3
import sys
import os

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add current directory to path for imports
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from api.interfaces import get_interfaces_data
from api.speedtest import router as speedtest_router
from api.settings import router as settings_router

app = FastAPI(title="Raspberry PI - Access Point")

# Mount static files - use absolute path
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates - use absolute path
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Include API routers
app.include_router(speedtest_router, prefix="/api", tags=["speedtest"])
app.include_router(settings_router, prefix="/api", tags=["settings"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/interfaces")
async def api_interfaces():
    """Get interfaces data - GET only, no POST"""
    try:
        data = get_interfaces_data()
        return data
    except Exception as e:
        return {
            "success": False,
            "error": f"Server error: {str(e)}"
        }


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})


@app.get("/system", response_class=HTMLResponse)
async def system(request: Request):
    """System page - placeholder"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/speedtest", response_class=HTMLResponse)
async def speedtest_page(request: Request):
    """Speed test page"""
    return templates.TemplateResponse("speedtest.html", {"request": request})

