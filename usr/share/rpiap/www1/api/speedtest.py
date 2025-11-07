#!/usr/bin/env python3
"""
Speed Test API endpoint
Accepts ping and download parameters
Returns JSON with success, message, and data fields
"""

import os
import binascii
from fastapi import APIRouter, Query, HTTPException

router = APIRouter()


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


@router.get("/api/speedtest")
async def speedtest(
    test: str = Query(..., description="Test type: 'ping' or 'download'"),
    size: int = Query(None, description="Size in bytes for download test (default: 1048576)"),
    id: int = Query(None, description="Chunk ID for download test (default: 1)")
):
    """
    Speed test endpoint
    - test=ping: Returns empty data for ping test
    - test=download: Generates random data and returns it with hash
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
            raise HTTPException(
                status_code=400,
                detail="Invalid test type. Use 'ping' or 'download'"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )

