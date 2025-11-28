#!/usr/bin/env python3
"""
Test router - handles test submenu endpoints
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


@router.get("/test/submenu")
async def test_submenu(request: Request) -> HTMLResponse:
    """Return HTML partial with test submenu items.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered test submenu partial.
    """
    # Get current_path from query parameter, fallback to request.url.path
    current_path = request.query_params.get("current_path", request.url.path)
    return templates.TemplateResponse(
        "partials/test_submenu.html",
        {
            "request": request,
            "current_path": current_path,
        }
    )
