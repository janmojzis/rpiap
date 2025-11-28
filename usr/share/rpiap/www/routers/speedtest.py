#!/usr/bin/env python3
"""
Speedtest router - handles /speedtest endpoint
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


@router.get("/speedtest", response_class=HTMLResponse)
async def speedtest(request: Request) -> HTMLResponse:
    """Speedtest page - returns full page or partial content based on query param.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered speedtest page or partial content.
    """
    from app import get_current_theme
    theme = get_current_theme(request)

    # Check if this is a partial request (HTMX content update)
    if request.query_params.get("partial") == "true":
        logger.debug("Speedtest: partial load - returning content area only")
        return templates.TemplateResponse("partials/speedtest_content.html", {
            "request": request,
            "css_theme": theme
        })

    # Full page load
    logger.debug("Speedtest: full load - returning index.html with speedtest_content")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/speedtest_content.html",
        "css_theme": theme
    })

