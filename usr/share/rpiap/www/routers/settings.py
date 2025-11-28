#!/usr/bin/env python3
"""
Settings router - handles settings pages and submenu
"""

import logging
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Setup templates
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/settings/submenu")
async def settings_submenu(request: Request) -> HTMLResponse:
    """Return HTML partial with settings submenu items.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered settings submenu partial.
    """
    # Get current_path from query parameter, fallback to request.url.path
    current_path = request.query_params.get("current_path", request.url.path)
    return templates.TemplateResponse(
        "partials/settings_submenu.html",
        {
            "request": request,
            "current_path": current_path,
        }
    )


@router.get("/settings/dns")
async def settings_dns(request: Request) -> HTMLResponse:
    """Return HTML page for DNS settings.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered DNS settings page.
    """
    from app import get_current_theme
    theme = get_current_theme(request)
    
    # Check if this is an HTMX request (partial content)
    # If partial=true query param or HX-Request header and target is content-area
    is_partial = request.query_params.get("partial") == "true"
    
    if is_partial:
        return templates.TemplateResponse("partials/settings_dns_content.html", {
            "request": request,
            "css_theme": theme
        })
        
    # Full page load
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/settings_dns_content.html",
        "css_theme": theme
    })


@router.get("/settings/wlan")
async def settings_wlan(request: Request) -> HTMLResponse:
    """Return HTML page for WLAN settings.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered WLAN settings page.
    """
    from app import get_current_theme
    theme = get_current_theme(request)
    
    # Check if this is an HTMX request (partial content)
    # If partial=true query param or HX-Request header and target is content-area
    is_partial = request.query_params.get("partial") == "true"
    
    if is_partial:
        return templates.TemplateResponse("partials/settings_wlan_content.html", {
            "request": request,
            "css_theme": theme
        })
        
    # Full page load
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/settings_wlan_content.html",
        "css_theme": theme
    })


@router.get("/settings/wcli")
async def settings_wcli(request: Request) -> HTMLResponse:
    """Return HTML page for Client settings.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered Client settings page.
    """
    from app import get_current_theme
    theme = get_current_theme(request)
    
    # Check if this is an HTMX request (partial content)
    # If partial=true query param or HX-Request header and target is content-area
    is_partial = request.query_params.get("partial") == "true"
    
    if is_partial:
        return templates.TemplateResponse("partials/settings_wcli_content.html", {
            "request": request,
            "css_theme": theme
        })
        
    # Full page load
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/settings_wcli_content.html",
        "css_theme": theme
    })


@router.get("/settings/mode")
async def settings_mode(request: Request) -> HTMLResponse:
    """Return HTML page for Mode settings.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered Mode settings page.
    """
    from app import get_current_theme
    theme = get_current_theme(request)
    
    # Check if this is an HTMX request (partial content)
    # If partial=true query param or HX-Request header and target is content-area
    is_partial = request.query_params.get("partial") == "true"
    
    if is_partial:
        return templates.TemplateResponse("partials/settings_mode_content.html", {
            "request": request,
            "css_theme": theme
        })
        
    # Full page load
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/settings_mode_content.html",
        "css_theme": theme
    })

