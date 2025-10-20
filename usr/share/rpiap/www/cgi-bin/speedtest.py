#!/usr/bin/env python3
"""
Simple Speed Test CGI Script
Accepts ping and download parameters
Returns JSON with success, message, and data fields
"""

import os
import sys
import json
import time
import hashlib
import binascii

def handle_ping():
    """Handle ping test - returns empty data"""
    return {
        "success": True,
        "message": "Ping test completed",
        "data": ""
    }

def handle_download():
    """Handle download test - returns hex encoded data"""
    # Get size parameter (default 1MB)
    size = 1048576  # Default 1MB
    
    # Parse query string for size parameter
    qs_list = os.environ.get('QUERY_STRING', '').split('&')
    for value in qs_list:
        if value.startswith('size='):
            try:
                size = int(value[5:])
                # Limit size to reasonable range (1KB to 10MB)
                size = max(1024, min(size, 10485760))
            except ValueError:
                size = 1048576  # Default if invalid
    
    # Generate pseudo-random data
    h = hashlib.shake_256(b"speedtest_seed")
    data = h.hexdigest(size//2)
    
    return {
        "success": True,
        "message": f"Download test completed - {size} bytes",
        "data": data
    }

def main():
    """Main function"""
    # Set JSON content type
    print("Content-Type: application/json")
    print()
    
    try:
        # Get test type from query string
        query_string = os.environ.get('QUERY_STRING', '')
        
        if 'test=ping' in query_string:
            result = handle_ping()
        elif 'test=download' in query_string:
            result = handle_download()
        else:
            result = {
                "success": False,
                "message": "Invalid test type. Use 'ping' or 'download'",
                "data": ""
            }
        
        # Output JSON
        #print(result)
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": ""
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
