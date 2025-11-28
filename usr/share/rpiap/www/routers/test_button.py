#!/usr/bin/env python3
"""
Test Button router - handles /test/button endpoint
"""

import logging
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Setup templates
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Env run directory path
ENV_RUN_DIR = "/run/rpiap/env"


@router.get("/test/button", response_class=HTMLResponse)
async def test_button_page(request: Request) -> HTMLResponse:
    """Test button page - returns full page or partial content based on query param.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered test button page or partial content.
    """
    from app import get_current_theme
    theme = get_current_theme(request)

    # Check if this is a partial request (HTMX content update)
    if request.query_params.get("partial") == "true":
        logger.debug("Test Button: partial load - returning content area only")
        return templates.TemplateResponse("partials/test_button_content.html", {
            "request": request,
            "css_theme": theme
        })

    # Full page load
    logger.debug("Test Button: full load - returning index.html with test_button_content")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/test_button_content.html",
        "css_theme": theme
    })


@router.post("/test/button/success")
async def test_button_success(request: Request) -> PlainTextResponse:
    """Trigger success bar display via HX-Trigger.

    Args:
        request: FastAPI request object.

    Returns:
        PlainTextResponse: Empty response with HX-Trigger header.
    """
    try:
        response = PlainTextResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "showSuccessBar"
        return response
    except Exception as e:
        logger.error("Error triggering success bar: %s", e)
        return PlainTextResponse(content="", status_code=500)


@router.post("/test/button/error")
async def test_button_error(request: Request) -> HTMLResponse:
    """Return error status bar HTML.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Error status bar HTML.
    """
    html = """<div class="errorbar" id="errorBar" hx-get="/api/errorbar/hide" hx-trigger="load delay:5s" hx-swap="outerHTML">
    <span class="statusbar__text">An error occurred during the operation.</span>
    <a hx-get="/api/errorbar/hide" hx-swap="outerHTML" class="statusbar__close" aria-label="Dismiss">×</a>
</div>"""
    return HTMLResponse(content=html)


@router.get("/test/status/hide")
async def status_hide(request: Request) -> HTMLResponse:
    """Return hidden status bar HTML.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Hidden status bar HTML.
    """
    html = """<div id="statusBar" hx-get="/api/successbar" hx-trigger="showSuccessBar from:body" hx-swap="outerHTML"></div>"""
    return HTMLResponse(content=html)


@router.post("/test/button/infobar/activate")
async def test_infobar_activate(request: Request) -> HTMLResponse:
    """Create test file in env directory to simulate env changes and trigger info bar refresh.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Empty response with HX-Trigger header.
    """
    try:
        # Create /run/rpiap/env directory if it doesn't exist
        if not os.path.exists(ENV_RUN_DIR):
            os.makedirs(ENV_RUN_DIR, mode=0o755)

        # Create test file to simulate env change
        test_file = os.path.join(ENV_RUN_DIR, "test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.chmod(test_file, 0o644)

        # Trigger infobar refresh
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "refreshInfoBar"
        return response
    except Exception as e:
        logger.error("Error activating test infobar: %s", e)
        return HTMLResponse(content="Error activating test infobar", status_code=500)


@router.post("/test/button/infobar/deactivate")
async def test_infobar_deactivate(request: Request) -> HTMLResponse:
    """Remove test file from env directory to simulate env reset and trigger info bar refresh.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Empty response with HX-Trigger header.
    """
    try:
        # Remove test file if it exists
        test_file = os.path.join(ENV_RUN_DIR, "test")
        if os.path.exists(test_file):
            os.remove(test_file)

        # Trigger infobar refresh
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "refreshInfoBar"
        return response
    except Exception as e:
        logger.error("Error deactivating test infobar: %s", e)
        return HTMLResponse(content="Error deactivating test infobar", status_code=500)
