#!/usr/bin/env python3
"""
Test Select router - handles /test/select endpoint
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")


@router.get("/test/select", response_class=HTMLResponse)
async def test_select_page(request: Request) -> HTMLResponse:
    """Test select page - returns full page or partial content based on query param.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered test select page or partial content.
    """
    from app import get_current_theme
    theme = get_current_theme(request)

    # Check if this is a partial request (HTMX content update)
    if request.query_params.get("partial") == "true":
        logger.debug("Test Select: partial load - returning content area only")
        return templates.TemplateResponse("partials/test_select_content.html", {
            "request": request,
            "css_theme": theme
        })

    # Full page load
    logger.debug("Test Select: full load - returning index.html with test_select_content")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/test_select_content.html",
        "css_theme": theme
    })

