#!/usr/bin/env python3
"""
Simple Speed Test CGI Script
Accepts ping and download parameters
Returns JSON or HTML with success, message, and data fields
"""

import os
import sys
import json
import time
import hashlib
import binascii
from urllib.parse import parse_qs

os.chdir("/var/lib/rpiap/empty")
os.chroot(".")

# Test state storage (simple file-based approach)
TEST_STATE_FILE = "/var/lib/rpiap/speedtest_state.json"

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
    chunk_id = 1  # Default chunk ID
    
    # Parse query string for size and id parameters
    qs_list = os.environ.get('QUERY_STRING', '').split('&')
    for value in qs_list:
        if value.startswith('size='):
            try:
                size = int(value[5:])
                # Limit size to reasonable range (1KB to 10MB)
                size = max(1024, min(size, 10485760))
            except ValueError:
                size = 1048576  # Default if invalid
        if value.startswith('id='):
            try:
                chunk_id = int(value[3:])
            except ValueError:
                chunk_id = 1  # Default if invalid
                
    # Generate pseudo-random data based on chunk ID
    #id_str = str(chunk_id).encode("utf-8")
    #h = hashlib.shake_256(id_str)
    #data = h.hexdigest(size//2)

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

def generate_html_results(ping=None, download_speed=None, progress=0, status="Ready to start"):
    """Generate HTML fragment for speed test results"""
    ping_display = f"{ping}" if ping is not None else "--"
    speed_display = f"{download_speed:.2f}" if download_speed is not None else "--"
    
    return f'''<div class="speed-metrics">
        <div class="metric-card">
            <h3>Download Speed</h3>
            <div class="metric-value" id="download-speed">{speed_display}</div>
            <div class="metric-unit">Mbps</div>
        </div>
        <div class="metric-card">
            <h3>Ping</h3>
            <div class="metric-value" id="ping-value">{ping_display}</div>
            <div class="metric-unit">ms</div>
        </div>
    </div>
    
    <div class="progress-container">
        <div class="progress-label">Test Progress</div>
        <div class="progress-bar">
            <div class="progress-fill" id="progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="progress-text" id="progress-text">{status}</div>
    </div>
    
    <div class="test-details" id="test-details">
        <h4>Test Details</h4>
        <div class="detail-item">
            <span class="detail-label">Test Duration:</span>
            <span class="detail-value" id="test-duration">--</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Data Transferred:</span>
            <span class="detail-value" id="data-transferred">--</span>
        </div>
    </div>'''

def main():
    """Main function"""
    query_string = os.environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    format_type = query_params.get('format', ['json'])[0]
    action = query_params.get('action', [''])[0]
    request_method = os.environ.get('REQUEST_METHOD', 'GET')
    
    try:
        if request_method == 'POST' and action == 'start' and format_type == 'html':
            # Start test - return initial HTML
            print("Content-Type: text/html\n")
            print(generate_html_results(status="Starting test...", progress=0))
            sys.exit(0)
        
        # Get test type from query string
        if 'test=ping' in query_string:
            result = handle_ping()
        elif 'test=download' in query_string:
            result = handle_download()
        elif format_type == 'html':
            # Return HTML results
            print("Content-Type: text/html\n")
            print(generate_html_results(status="Test in progress...", progress=50))
            sys.exit(0)
        else:
            result = {
                "success": False,
                "message": "Invalid test type. Use 'ping' or 'download'",
                "data": ""
            }
        
        # Output JSON
        if format_type == 'html':
            print("Content-Type: text/html\n")
            ping = result.get('ping') if 'ping' in result else None
            download = result.get('download_speed') if 'download_speed' in result else None
            print(generate_html_results(ping=ping, download_speed=download, progress=100, status="Test completed"))
        else:
            print("Content-Type: application/json\n")
            print(json.dumps(result))
        
    except Exception as e:
        if format_type == 'html':
            print("Content-Type: text/html\n")
            error_html = f'''<div class="status-bar error visible" id="statusBar" hx-swap-oob="true">
                <span id="statusMessage">Speed test error: {str(e)}</span>
                <button class="status-close" onclick="document.getElementById('statusBar').classList.remove('visible')">×</button>
            </div>'''
            print(error_html)
        else:
            error_result = {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": ""
            }
            print("Content-Type: application/json\n")
            print(json.dumps(error_result))

if __name__ == "__main__":
    main()
