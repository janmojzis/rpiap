#!/usr/bin/env python3
"""
Errorbar router - handles /api/errorbar endpoints
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/errorbar/show")
async def errorbar_show(request: Request) -> PlainTextResponse:
    """Trigger error bar display via HX-Trigger.

    Args:
        request: FastAPI request object.

    Returns:
        PlainTextResponse: Empty response with HX-Trigger header.
    """
    try:
        response = PlainTextResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "showErrorBar"
        return response
    except Exception as e:
        logger.error("Error triggering error bar: %s", e)
        return PlainTextResponse(content="", status_code=500)


@router.get("/api/errorbar")
async def errorbar_get(request: Request, message: str = "An error occurred during the operation") -> PlainTextResponse:
    """Return error bar message as plain text.

    Args:
        request: FastAPI request object.
        message: Custom message to display (optional).

    Returns:
        PlainTextResponse: Error message as plain text.
    """
    try:
        return PlainTextResponse(content=message, status_code=200)
    except Exception as e:
        logger.error("Error rendering error bar: %s", e)
        return PlainTextResponse(content="", status_code=500)


@router.get("/api/errorbar/hide")
async def errorbar_hide(request: Request) -> PlainTextResponse:
    """Return empty text to hide error bar.

    Args:
        request: FastAPI request object.

    Returns:
        PlainTextResponse: Empty text to clear the bar.
    """
    try:
        return PlainTextResponse(content="", status_code=200)
    except Exception as e:
        logger.error("Error hiding error bar: %s", e)
        return PlainTextResponse(content="", status_code=500)
