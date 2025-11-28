#!/usr/bin/env python3
"""
Test UI router - handles /test/ui endpoint with UI components gallery
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


@router.get("/test/ui", response_class=HTMLResponse)
async def test_ui_page(request: Request) -> HTMLResponse:
    """Test UI page - returns full page or partial content with UI components gallery.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered test UI page or partial content.
    """
    from app import get_current_theme
    theme = get_current_theme(request)

    # Check if this is a partial request (HTMX content update)
    if request.query_params.get("partial") == "true":
        logger.debug("Test UI: partial load - returning content area only")
        return templates.TemplateResponse("partials/test_ui_content.html", {
            "request": request,
            "css_theme": theme
        })

    # Full page load
    logger.debug("Test UI: full load - returning index.html with test_ui content")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/test_ui_content.html",
        "css_theme": theme
    })
