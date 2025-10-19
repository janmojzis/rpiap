#!/usr/bin/env python3
"""
Services management CGI script for rpiap
Handles GET requests for service status and POST requests for service restart
"""

import cgi
import json
import os
import sys
import random

def get_services_status():
    """
    Get status of all services
    Returns a list of service dictionaries with name and status
    """
    # Mock service data - in real implementation, this would check actual service status
    services = [
        {"name": "httpd", "status": "down"},
        {"name": "hostapd", "status": "up"},
        {"name": "udhcpd", "status": "up"},
        {"name": "radvd", "status": "down"},
        {"name": "wpasupplicant_eth0", "status": "up"},
        {"name": "wpasupplicant_wlan1", "status": "down"},
        {"name": "ifupdownd", "status": "up"},
        {"name": "pqconnect", "status": "up"},
        {"name": "dqcache", "status": "down"}
    ]
    
    return services

def restart_service(service_name):
    """
    Restart a specific service
    Returns success/failure status randomly for testing
    """
    # In real implementation, this would actually restart the service
    # For now, return random success/failure for testing
    success = random.choice([True, False])
    
    if success:
        return {"success": True, "message": f"Service {service_name} restarted successfully"}
    else:
        return {"success": False, "message": f"Failed to restart service {service_name}"}

def start_service(service_name):
    """
    Start a specific service
    Returns success/failure status randomly for testing
    """
    # In real implementation, this would actually start the service
    # For now, return random success/failure for testing
    success = random.choice([True, False])
    
    if success:
        return {"success": True, "message": f"Service {service_name} started successfully"}
    else:
        return {"success": False, "message": f"Failed to start service {service_name}"}

def stop_service(service_name):
    """
    Stop a specific service
    Returns success/failure status randomly for testing
    """
    # In real implementation, this would actually stop the service
    # For now, return random success/failure for testing
    success = random.choice([True, False])
    
    if success:
        return {"success": True, "message": f"Service {service_name} stopped successfully"}
    else:
        return {"success": False, "message": f"Failed to stop service {service_name}"}

def handle_get_request():
    """Handle GET request - return service status"""
    try:
        services = get_services_status()
        response = {
            "success": True,
            "services": services
        }
        return response
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get service status: {str(e)}"
        }

def handle_post_request():
    """Handle POST request - service operations"""
    try:
        # Parse form data
        form = cgi.FieldStorage()
        
        if 'service' not in form:
            return {
                "success": False,
                "error": "Service name not provided"
            }
        
        service_name = form['service'].value
        action = form.getvalue('action', 'restart').strip()  # Default to restart for backward compatibility
        
        # Perform the requested action
        if action == 'restart':
            result = restart_service(service_name)
        elif action == 'start':
            result = start_service(service_name)
        elif action == 'stop':
            result = stop_service(service_name)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to perform service operation: {str(e)}"
        }

def main():
    """Main CGI handler"""
    # Set content type
    print("Content-Type: application/json")
    print()
    
    try:
        # Get request method
        method = os.environ.get('REQUEST_METHOD', 'GET')
        
        if method == 'GET':
            response = handle_get_request()
        elif method == 'POST':
            response = handle_post_request()
        else:
            response = {
                "success": False,
                "error": f"Unsupported method: {method}"
            }
        
        # Output JSON response
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }
        print(json.dumps(error_response, indent=2))

if __name__ == '__main__':
    main()
