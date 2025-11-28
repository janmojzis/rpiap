#!/usr/bin/env python3
"""
Successbar router - handles /api/successbar endpoints
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/successbar/show")
async def successbar_show(request: Request) -> PlainTextResponse:
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


@router.get("/api/successbar")
async def successbar_get(request: Request, message: str = "Operation completed successfully") -> PlainTextResponse:
    """Return success bar message as plain text.

    Args:
        request: FastAPI request object.
        message: Custom message to display (optional).

    Returns:
        PlainTextResponse: Success message as plain text.
    """
    try:
        return PlainTextResponse(content=message, status_code=200)
    except Exception as e:
        logger.error("Error rendering success bar: %s", e)
        return PlainTextResponse(content="", status_code=500)


@router.get("/api/successbar/hide")
async def successbar_hide(request: Request) -> PlainTextResponse:
    """Return empty text to hide success bar.

    Args:
        request: FastAPI request object.

    Returns:
        PlainTextResponse: Empty text to clear the bar.
    """
    try:
        return PlainTextResponse(content="", status_code=200)
    except Exception as e:
        logger.error("Error hiding success bar: %s", e)
        return PlainTextResponse(content="", status_code=500)
