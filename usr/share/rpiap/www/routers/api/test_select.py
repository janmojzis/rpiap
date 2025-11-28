#!/usr/bin/env python3
"""
Test Select API endpoint
"""

import asyncio
from fastapi import APIRouter, Request, Form
from fastapi import status as http_status
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.post("/test/select")
async def test_select_submit(request: Request, status: str = Form(...)):
    """Handle select form submission - returns appropriate HTTP status code"""
    # Check for exception
    if status == "exception":
        # Simulate Python script exception - raise exception (returns 500)
        raise Exception("Python script raised an exception: Unhandled error occurred.")
    
    # Check for timeout - never returns response
    if status == "timeout":
        # Simulate real timeout - wait indefinitely
        await asyncio.sleep(float('inf'))
    
    # Return appropriate HTTP status codes with minimal HTML - status-target.js will handle display
    if status == "success":
        return HTMLResponse(content="<!-- success -->", status_code=http_status.HTTP_200_OK)
    elif status == "failure":
        return HTMLResponse(content="<!-- failure -->", status_code=http_status.HTTP_400_BAD_REQUEST)
    elif status == "disabled":
        return HTMLResponse(content="<!-- disabled -->", status_code=http_status.HTTP_403_FORBIDDEN)
    
    # Default to 200 OK
    return HTMLResponse(content="<!-- default -->", status_code=http_status.HTTP_200_OK)

