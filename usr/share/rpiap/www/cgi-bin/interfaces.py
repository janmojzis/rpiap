#!/usr/bin/env python3
import os
import json
import psutil
import socket
import ipaddress
import struct
import fcntl
import logging
import cgi
from urllib.parse import parse_qs


os.chdir("/sys")
os.chroot(".")

SIOCGIFFLAGS = 0x8913  # get flags
SIOCSIFFLAGS = 0x8914  # set flags
IFF_UP = 0x1
IFF_RUNNING = 0x40

def if_downup(ifname: str) -> None:

    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # get flags
    ifreq = struct.pack('256s', ifname[:15].encode('utf-8'))
    res = fcntl.ioctl(s, SIOCGIFFLAGS, ifreq)
    flags = struct.unpack('H', res[16:18])[0]

    # unset IFF_UP
    flags &= ~IFF_UP
    ifreq = struct.pack('16sH', ifname[:15].encode('utf-8'), flags)
    fcntl.ioctl(s, SIOCSIFFLAGS, ifreq)

    # set IFF_UP
    flags |= IFF_UP
    ifreq = struct.pack('16sH', ifname[:15].encode('utf-8'), flags)
    fcntl.ioctl(s, SIOCSIFFLAGS, ifreq)

    s.close()

def wan_get() -> str | None:
    """
    use trick how to get local IP - try external connection
    """
    ip = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        try:
            s.connect(("1.1.1.1", 53))
            ip = s.getsockname()[0]
        except (OSError, socket.error):
            # If it fails (no internet connection)
            pass
    finally:
        s.close()

    if ip is not None:
        interfaces = psutil.net_if_addrs()
        for ifname, addrs in interfaces.items():
            for addr in addrs:
                if addr.address == ip:
                    return ifname

    return None


def bridge_list(ifname: str) -> list[str]:
    """
    """

    return os.listdir(f"/class/net/{ifname}/brif/")

def ipv4_to_cidr(addr: str, mask: str) -> str:
    prefixlen = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    return f"{addr}/{prefixlen}"

def ipv6_to_cidr(addr: str, mask: str) -> str:
    mask_addr = ipaddress.IPv6Address(mask)
    bits = bin(int(mask_addr))[2:].zfill(128)
    prefixlen = bits.count("1")
    return f"{addr}/{prefixlen}"

def ifaces_get() -> dict:
    ret = {}
    interfaces = psutil.net_if_addrs()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        for ifname, addrs in interfaces.items():
            ret[ifname] = {}
            ret[ifname]["ipv4"] = []
            ret[ifname]["ipv6"] = []
            ret[ifname]["active"] = False
            ret[ifname]["interface"] = ifname

            for addr in addrs:
                # MAC address
                if addr.family == psutil.AF_LINK:
                    ret[ifname]["mac"] = addr.address
                # IPv4
                if addr.family.name == "AF_INET" and addr.address:
                    ret[ifname]["ipv4"].append(ipv4_to_cidr(addr.address, addr.netmask))
                # IPv6
                elif addr.family.name == "AF_INET6" and addr.address:
                    clean_addr = str(addr.address)
                    if clean_addr.startswith("fe80:"):
                        continue
                    clean_addr = clean_addr.split("%")[0]  # remove %eth0 from address
                    ret[ifname]["ipv6"].append(ipv6_to_cidr(clean_addr, addr.netmask))

            # flags - check once per interface, not per address
            ifname_bytes = ifname.encode("utf-8")
            ifreq = struct.pack("16sH14s", ifname_bytes, 0, b"")
            try:
                out = fcntl.ioctl(s.fileno(), SIOCGIFFLAGS, ifreq)
                _, flags, _ = struct.unpack("16sH14s", out)
                if not (flags & IFF_UP):
                    ret[ifname]["state"] = "down"
                elif flags & IFF_RUNNING:
                    ret[ifname]["state"] = "up"
                else:
                    ret[ifname]["state"] = "down"  # lowerlayerdown
            except Exception:
                ret[ifname]["state"] = "unknown"


    finally:
        s.close()

    return ret

def get_interface_data():
    """Get structured interface data"""
    # ALL interfaces
    ifaces = ifaces_get()

    # LAN interfaces
    lan_ifnames = bridge_list("lan")
    lan = ifaces["lan"]
    lan["active"] = True
    lan["interfaces"] = []
    del lan["state"]
    del lan["interface"]
    for ifname in ifaces:
        if ifname in lan_ifnames:
            del ifaces[ifname]["ipv4"]
            del ifaces[ifname]["ipv6"]
            del ifaces[ifname]["active"]
            lan["interfaces"].append(ifaces[ifname])

    # WAN interfaces
    wan_ifname = wan_get()
    wan = {}
    other = {}
    if wan_ifname is not None:
        wan["active"] = True
    else:
        wan["active"] = False
    wan["interfaces"] = []
    other["interfaces"] = []
    for ifname in ifaces:
        if ifname in lan_ifnames:
            continue
        if ifname in ["eth0", "eth1", "eth2", "wlan1", "usb0"]:
            del ifaces[ifname]["active"]
            if ifname == wan_ifname:
                wan["ipv4"] = ifaces[ifname]["ipv4"]
                wan["ipv6"] = ifaces[ifname]["ipv6"]
                del ifaces[ifname]["ipv4"]
                del ifaces[ifname]["ipv6"]
                wan["interfaces"].append(ifaces[ifname])
            else:
                del ifaces[ifname]["ipv4"]
                del ifaces[ifname]["ipv6"]
                other["interfaces"].append(ifaces[ifname])

    return {"wan": wan, "lan": lan, "other": other}

def generate_interface_card(interface_data, card_type):
    """Generate HTML for a single interface card"""
    is_online = interface_data.get("state") == "up"
    is_active = interface_data.get("active", False)
    mac = interface_data.get("mac", "N/A")
    
    card_class = f"{card_type}-interface-card"
    if is_active:
        card_class += " active"
    elif not is_online:
        card_class += " offline"
    
    return f'''<div class="{card_class}" data-interface="{interface_data['interface']}">
                <div class="interface-header">
                    <h4>{interface_data['interface']}</h4>
                    <span class="status-indicator {'online' if is_online else 'offline'}"></span>
                </div>
                <div class="interface-details">
                    <p>MAC: {mac}</p>
                    <p>Status: {'Online' if is_online else 'Offline'}</p>
                    {('<p style="color: #4CAF50; font-size: 12px; margin-top: 8px;">Drag to WAN to use</p>' if (card_type == 'other' and is_online) else '')}
                </div>
            </div>'''

def generate_html_dashboard():
    """Generate HTML fragment for dashboard"""
    data = get_interface_data()
    wan = data["wan"]
    lan = data["lan"]
    other = data["other"]
    
    # LAN IP addresses
    lan_ipv4 = lan.get("ipv4", [])
    lan_ipv4_str = lan_ipv4[0] if lan_ipv4 else "N/A"
    lan_ipv6 = lan.get("ipv6", [])
    lan_ipv6_str = lan_ipv6[0] if lan_ipv6 else "N/A"
    lan_active = lan.get("active", False)
    
    # WAN IP addresses
    wan_ipv4 = wan.get("ipv4", [])
    wan_ipv4_str = wan_ipv4[0] if wan_ipv4 else "N/A"
    wan_ipv6 = wan.get("ipv6", [])
    wan_ipv6_str = wan_ipv6[0] if wan_ipv6 else "N/A"
    wan_active = wan.get("active", False)
    
    # Generate interface cards
    lan_cards = "".join([generate_interface_card(iface, "lan") for iface in lan.get("interfaces", [])])
    wan_cards = "".join([generate_interface_card(iface, "wan") for iface in wan.get("interfaces", [])])
    other_cards = "".join([generate_interface_card(iface, "other") for iface in other.get("interfaces", [])])
    
    # Card classes
    lan_card_class = "card lan-active" if lan_active else "card lan-inactive"
    wan_card_class = "card wan-active" if wan_active else "card wan-inactive"
    
    html = f'''<div class="{lan_card_class}" id="lan-card">
            <h3>LAN Interfaces</h3>
            <p>IPv4: <span id="lan-ipv4">{lan_ipv4_str}</span></p>
            <p>IPv6: <span id="lan-ipv6">{lan_ipv6_str}</span></p>
            <div class="lan-interfaces-grid" id="lan-interfaces-container">
                {lan_cards if lan_cards else '<div class="loading-message">No LAN interfaces</div>'}
            </div>
        </div>
        <div class="{wan_card_class}" id="wan-card">
            <h3>WAN Interfaces</h3>
            <p>IPv4: <span id="wan-ipv4">{wan_ipv4_str}</span></p>
            <p>IPv6: <span id="wan-ipv6">{wan_ipv6_str}</span></p>
            <div class="wan-interfaces-grid" id="wan-interfaces-container">
                {wan_cards if wan_cards else '<div class="loading-message">No WAN interfaces</div>'}
            </div>
        </div>
        <div class="card" id="other-card">
            <h3>Other Interfaces</h3>
            <div class="other-interfaces-grid" id="other-interfaces-container">
                {other_cards if other_cards else '<div class="loading-message">No other interfaces</div>'}
            </div>
        </div>'''
    
    return html

def handle_get():
    """Handle GET request - return all data"""
    data = get_interface_data()
    response = {
        "success": True,
        "wan": data["wan"],
        "lan": data["lan"],
        "other": data["other"],
    }
    return response

def handle_post():
    """Handle POST request - switch WAN interface only"""
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
        ifaces = ifaces_get()
        
        # Only allow WAN interfaces for switching
        wan_interfaces = {}
        for ifname in ifaces:
            if ifname in ["eth0", "eth1", "wlan1", "usb0"]:
                wan_interfaces[ifname] = ifaces[ifname]
        
        # Find interface in WAN list only
        if interface_name not in wan_interfaces:
            return {
                "success": False,
                "error": f"WAN Interface {interface_name} not found. Only WAN interfaces can be switched."
            }
        
        interface_found = wan_interfaces[interface_name]
        
        # Update active interface
        logging.debug(f"Set active interface {interface_name}")
        if_downup(interface_name)
        
        # Return updated data using get_interface_data
        data = get_interface_data()
        return {
            "success": True,
            "message": f"Successfully switched to {interface_name}",
            "wan": data["wan"],
            "lan": data["lan"],
            "other": data["other"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing request: {str(e)}"
        }

if __name__ == "__main__":
    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.DEBUG)

    # Check format parameter
    query_string = os.environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    format_type = query_params.get('format', ['json'])[0]
    
    try:
        if os.environ.get('REQUEST_METHOD') == 'POST':
            response = handle_post()
            
            if format_type == 'html':
                # Return HTML fragment with updated dashboard
                print("Content-Type: text/html\n")
                
                # Generate status message
                if response.get("success"):
                    status_msg = response.get("message", "Operation successful")
                    status_type = "success"
                else:
                    status_msg = response.get("error", "Operation failed")
                    status_type = "error"
                
                # Status bar HTML
                status_html = f'''<div class="status-bar {status_type} visible" id="statusBar" hx-swap-oob="true">
                    <span id="statusMessage">{status_msg}</span>
                    <button class="status-close" onclick="document.getElementById('statusBar').classList.remove('visible')">×</button>
                </div>'''
                
                # Dashboard HTML
                data = get_interface_data()
                dashboard_html = generate_html_dashboard()
                
                print(status_html + dashboard_html)
            else:
                # Return JSON
                print("Content-Type: application/json\n")
                print(json.dumps(response, indent=2))
        else:
            # GET request
            if format_type == 'html':
                print("Content-Type: text/html\n")
                print(generate_html_dashboard())
            else:
                # Return JSON
                response = handle_get()
                print("Content-Type: application/json\n")
                print(json.dumps(response, indent=2))

    except Exception as e:
        if format_type == 'html':
            print("Content-Type: text/html\n")
            error_html = f'''<div class="status-bar error visible" id="statusBar" hx-swap-oob="true">
                <span id="statusMessage">Server error: {str(e)}</span>
                <button class="status-close" onclick="document.getElementById('statusBar').classList.remove('visible')">×</button>
            </div>'''
            print(error_html)
        else:
            error_response = {
                "success": False,
                "error": f"Server error: {str(e)}"
            }
            print("Content-Type: application/json\n")
            print(json.dumps(error_response, indent=2))
