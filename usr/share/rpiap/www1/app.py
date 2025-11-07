#!/usr/bin/env python3
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from api.interfaces import get_interfaces_data
from api.speedtest import router as speedtest_router

app = FastAPI(title="Raspberry PI - Access Point")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(speedtest_router)


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


# Placeholder routes for future implementation
@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page - placeholder"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/system", response_class=HTMLResponse)
async def system(request: Request):
    """System page - placeholder"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/speedtest", response_class=HTMLResponse)
async def speedtest_page(request: Request):
    """Speed test page"""
    return templates.TemplateResponse("speedtest.html", {"request": request})

