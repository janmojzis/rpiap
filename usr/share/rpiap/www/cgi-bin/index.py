#!/usr/bin/env python3
import json
import sys
import os
import cgi
import ipaddress
import psutil

def netmask_to_prefix(netmask):
    return ipaddress.IPv4Network(f"0.0.0.0/{netmask}").prefixlen

def ipv6_netmask_to_prefix(mask: str) -> int:
    addr = ipaddress.IPv6Address(mask)
    bits = bin(int(addr))[2:].zfill(128)
    prefixlen = bits.find('0')
    if prefixlen == -1:
        prefixlen = 128
    return prefixlen

def get_ip_info():
    result = []
    
    # Use psutil for real network interface detection
    interfaces = psutil.net_if_addrs()

    try:
        iface_active = open(f'/var/lib/rpiap/service/udhcpc/env/IFACE').read().strip()
    except:
        iface_active = "none"
    
    for iface, addrs in interfaces.items():
        ipv4 = ""
        ipv6 = ""

        if iface not in ["eth0", "wlan1", "eth1", "usb0"]:
            continue

        for addr in addrs:
            # IPv4
            if addr.family.name == 'AF_INET' and addr.address:
                prefix = netmask_to_prefix(addr.netmask)
                if prefix is not None:
                    ipv4 = f"{addr.address}/{prefix}"
            # IPv6
            elif addr.family.name == 'AF_INET6' and addr.address:
                clean_addr = addr.address.split('%')[0]
                if clean_addr.startswith("fe80:"):
                    continue
                prefix = ipv6_netmask_to_prefix(addr.netmask)
                if prefix is not None:
                    ipv6 = f"{clean_addr}/{prefix}"

        try:
            link = open(f'/sys/class/net/{iface}/operstate').read().strip()
            device = 'up'
        except FileNotFoundError:
            link = 'down'
            device = 'down'

        if iface_active == iface:
            active = True
        else:
            active = False
            
        result.append({
            "interface": iface,
            "ip4": ipv4,
            "ip6": ipv6,
            "link": link,
            "device": device,
            "active": active
        })

    return result

# Set content type for JSON response
print("Content-Type: application/json\n")

# WLAN data
wlan_data = {
    "ssid": "rpiap",
    "ip": "192.168.137.1/24",
    "ipv6": "fd::1/64"
}


def handle_get():
    """Handle GET request - return all data"""
    
    response = {
        "success": True,
        "wan_interfaces": get_ip_info(),
        "wlan": wlan_data
    }
    return response

def handle_post():
    """Handle POST request - switch WAN interface"""
    try:
        # Parse form data
        form = cgi.FieldStorage()
        
        if 'interface' not in form:
            return {
                "success": False,
                "error": "Missing interface parameter"
            }
        
        interface_name = form['interface'].value.strip()
        
        # Get current interfaces
        wan_interfaces = get_ip_info()
        
        # Find interface in list
        interface_found = None
        for iface in wan_interfaces:
            if iface["interface"] == interface_name:
                interface_found = iface
                break
        
        if not interface_found:
            return {
                "success": False,
                "error": f"Interface {interface_name} not found"
            }
        
        # Check if interface is up
        if interface_found["link"] != "up" or interface_found["device"] != "up":
            return {
                "success": False,
                "error": f"Cannot switch to {interface_name} - interface is down"
            }
        
        # Update active interface
        with open(f'/var/lib/rpiap/service/udhcpc/env/IFACE', 'w') as f:
            f.write(interface_name)
        with open(f'/var/lib/rpiap/service/udhcpc/supervise/control', 'w') as f:
            f.write("t")
        
        return {
            "success": True,
            "message": f"Successfully switched to {interface_name}",
            "wan_interfaces": get_ip_info()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing request: {str(e)}"
        }


# Main logic
try:
    if os.environ.get('REQUEST_METHOD') == 'POST':
        response = handle_post()
    else:
        response = handle_get()
    
    print(json.dumps(response, indent=2))
    
except Exception as e:
    error_response = {
        "success": False,
        "error": f"Server error: {str(e)}"
    }
    print(json.dumps(error_response, indent=2))
