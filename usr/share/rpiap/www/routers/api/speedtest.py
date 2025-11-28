#!/usr/bin/env python3
"""
Speed Test API endpoint
Accepts ping and download parameters
Returns JSON with success, message, and data fields
"""

import os
import binascii
import time
import json
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup templates - use absolute path
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)


def handle_ping():
    """Handle ping test - returns empty data"""
    return {
        "success": True,
        "message": "Ping test completed",
        "data": ""
    }


def handle_download(size: int = 1048576, chunk_id: int = 1):
    """Handle download test - returns hex encoded data"""
    # Limit size to reasonable range (1KB to 10MB)
    size = max(1024, min(size, 10485760))
    
    # Generate random data
    data = binascii.hexlify(os.urandom(size//2)).decode('utf-8')
    
    # Calculate hash of the generated data (same algorithm as JavaScript)
    data_hash = 0
    if len(data) > 0:
        for char in data:
            data_hash = ((data_hash << 5) - data_hash) + ord(char)
            data_hash = data_hash & 0xFFFFFFFF  # Convert to 32-bit unsigned integer
    
    # Convert to positive hex string (8 characters)
    data_hash_hex = format(data_hash, '08x')
    
    return {
        "success": True,
        "message": f"Download test completed - {size} bytes (chunk {chunk_id})",
        "data": data,
        "hash": data_hash_hex
    }


@router.get("/speedtest", response_class=JSONResponse)
async def speedtest(
    request: Request,
    test: str = Query(..., description="Test type: 'ping' or 'download'"),
    size: int = Query(None, description="Size in bytes for download test (default: 1048576)"),
    id: int = Query(None, description="Chunk ID for download test (default: 1)")
):
    """
    Speed test endpoint - legacy JSON format for backward compatibility
    """
    try:
        if test == "ping":
            result = handle_ping()
        elif test == "download":
            # Use defaults if not provided
            download_size = size if size is not None else 1048576
            chunk_id = id if id is not None else 1
            result = handle_download(download_size, chunk_id)
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Invalid test type. Use 'ping' or 'download'",
                "data": ""
            })
        
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"Error: {str(e)}",
            "data": ""
        })


@router.get("/speedtest/ping", response_class=HTMLResponse)
async def speedtest_ping(request: Request):
    """Ping test endpoint - returns HTML with ping result"""
    try:
        start_time = time.time()
        # Simulate ping - just return immediately
        ping_time = int((time.time() - start_time) * 1000)
        
        return templates.TemplateResponse("partials/speedtest_results.html", {
            "request": request,
            "ping_value": ping_time,
            "download_speed": None,
            "progress": 100,
            "progress_text": "Ping test completed",
            "test_duration": f"{ping_time}ms",
            "data_transferred": "0 bytes"
        })
    except Exception as e:
        return HTMLResponse(content=f"<div class='alert alert--error'>Error: {str(e)}</div>", status_code=500)


@router.get("/speedtest/download", response_class=HTMLResponse)
async def speedtest_download(
    request: Request,
    size: int = Query(1048576, description="Size in bytes for download test"),
    chunk_id: int = Query(1, description="Chunk ID for download test")
):
    """Download test endpoint - returns HTML with download result"""
    try:
        start_time = time.time()
        # Limit size to reasonable range (1KB to 10MB)
        size = max(1024, min(size, 10485760))
        
        # Generate random data
        data = binascii.hexlify(os.urandom(size//2)).decode('utf-8')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate speed in Mbps
        speed_mbps = (size * 8) / (duration * 1000000) if duration > 0 else 0
        
        return templates.TemplateResponse("partials/speedtest_results.html", {
            "request": request,
            "ping_value": None,
            "download_speed": f"{speed_mbps:.2f}",
            "progress": 100,
            "progress_text": f"Download test completed - {size} bytes",
            "test_duration": f"{duration:.2f}s",
            "data_transferred": f"{size} bytes"
        })
    except Exception as e:
        return HTMLResponse(content=f"<div class='alert alert--error'>Error: {str(e)}</div>", status_code=500)

