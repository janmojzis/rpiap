#!/usr/bin/env python3
"""
Home router - handles /api/sidebar endpoint
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")


@router.get("/api/sidebar/update")
async def sidebar_update(request: Request) -> HTMLResponse:
    """Return updated sidebar based on current path.

    Args:
        request: FastAPI request object.

    Returns:
        HTMLResponse: Rendered sidebar partial.
    """
    current_path = str(request.query_params.get("current_path", request.url.path))
    logger.debug("Sidebar update requested for path: %s", current_path)
    return templates.TemplateResponse("partials/sidebar.html", {
        "request": request,
        "current_path": current_path
    })

