#!/usr/bin/env python3
"""
Home router - handles / endpoint
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Home page - returns full page or partial content based on query param.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered home page or partial content.
    """
    from app import get_current_theme
    theme = get_current_theme(request)

    # Check if this is a partial request (HTMX content update)
    if request.query_params.get("partial") == "true":
        logger.debug("Home: partial load - returning content area only")
        return templates.TemplateResponse("partials/home_content.html", {
            "request": request,
            "css_theme": theme
        })

    # Full page load
    logger.debug("Home: full load - returning index.html with home_content")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "content_template": "partials/home_content.html",
        "css_theme": theme
    })
