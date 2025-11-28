#!/usr/bin/env python3
import os
import sys
import psutil
import socket
import ipaddress
import struct
import fcntl
import json
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup templates - use absolute path
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter()

# LAN env file path
LAN_ENV_FILE = "/var/lib/rpiap/env/lan"
allowed_interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "usb0"]

SIOCGIFFLAGS = 0x8913  # get flags
SIOCSIFFLAGS = 0x8914  # set flags
IFF_UP = 0x1
IFF_RUNNING = 0x40


def if_downup(ifname: str) -> None:
    """Activate interface by doing down/up cycle"""
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


def if_ip4_isactive(name: str) -> bool:
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
                    return ifname == name

    return False


def if_ip6_isactive(name: str) -> bool:
    """         
    use trick how to get local IP - try external connection
    """             
    ip = None       
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:            
        try:        
            s.connect(("2606:4700:4700::1111", 53))
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
                    return ifname == name

    return False


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


def get_interfaces_data():
    """Get all interfaces data - return same structure as CGI script"""
    # Load LAN interfaces from env file each call
    if os.path.exists(LAN_ENV_FILE):
        with open(LAN_ENV_FILE) as f:
            lan_interfaces = f.read().strip().split("\n")
    else:
        lan_interfaces = ["wlan0"]

    # ALL interfaces
    ifaces = ifaces_get()

    # LAN interfaces
    lan = ifaces.get("lan", {})
    lan["interfaces"] = []
    lan["ipv4active"] = len(lan.get("ipv4", [])) > 0
    lan["ipv6active"] = len(lan.get("ipv6", [])) > 0
    for ifname in lan_interfaces:
        tmp = {}
        try:
            tmp["state"] = ifaces[ifname]["state"]
            tmp["interface"] = ifaces[ifname]["interface"]
            tmp["mac"] = ifaces[ifname].get("mac", "N/A")
            tmp["active"] = tmp["state"] == "up"
        except KeyError:
            # interface is down
            tmp["state"] = "down"
            tmp["interface"] = ifname
            tmp["active"] = False
        lan["interfaces"].append(tmp)

    # WAN/OTHER interfaces
    wan = {}
    other = {}
    wan["interfaces"] = []
    other["interfaces"] = []
    active_interfaces = set()  # Track which interfaces are active (go to WAN)

    for ifname in ifaces:
        if ifname in lan_interfaces or ifname == "lan":
            continue
        if ifname in allowed_interfaces:
            ifaces[ifname]["ipv4active"] = if_ip4_isactive(ifname)
            ifaces[ifname]["ipv6active"] = if_ip6_isactive(ifname)
            ifaces[ifname]["active"] = ifaces[ifname]["ipv6active"] or ifaces[ifname]["ipv4active"]
            if ifaces[ifname]["ipv6active"] or ifaces[ifname]["ipv4active"]:
                wan["interfaces"].append(ifaces[ifname])
                active_interfaces.add(ifname)
            else:
                other["interfaces"].append(ifaces[ifname])

    # Add all allowed interfaces not in LAN and not active to "other"
    for ifname in allowed_interfaces:
        if ifname not in lan_interfaces and ifname not in active_interfaces:
            if ifname not in [iface["interface"] for iface in other["interfaces"]]:
                # Add interface to other if not already there
                if ifname in ifaces:
                    iface_data = ifaces[ifname].copy()
                    iface_data["ipv4active"] = if_ip4_isactive(ifname)
                    iface_data["ipv6active"] = if_ip6_isactive(ifname)
                    iface_data["active"] = iface_data["ipv6active"] or iface_data["ipv4active"]
                    other["interfaces"].append(iface_data)
                else:
                    # Interface not detected by psutil, add with down state
                    other["interfaces"].append({
                        "interface": ifname,
                        "state": "down",
                        "ipv4": [],
                        "ipv6": [],
                        "ipv4active": False,
                        "ipv6active": False,
                        "active": False
                    })

    response = {
        "success": True,
        "wan": wan,
        "lan": lan,
        "other": other,
    }
    return response


def get_wan_active_status(data):
    """Determine if WAN is active based on interfaces"""
    wan = data.get("wan", {})
    interfaces = wan.get("interfaces", [])
    return any(iface.get("ipv4active") or iface.get("ipv6active") for iface in interfaces)


def extract_lan_info(data):
    """Extract LAN IP info from data"""
    lan = data.get("lan", {})
    ipv4_list = lan.get("ipv4", [])
    ipv6_list = lan.get("ipv6", [])
    lan_ipv4 = ipv4_list[0] if ipv4_list else None
    lan_ipv6 = ipv6_list[0] if ipv6_list else None
    return {
        "lan_ipv4": lan_ipv4,
        "lan_ipv6": lan_ipv6,
        "lan_ipv4active": lan.get("ipv4active", False),
        "lan_ipv6active": lan.get("ipv6active", False),
        "lan_active": lan.get("ipv4active", False) or lan.get("ipv6active", False)
    }


@router.get("/interfaces/wan", response_class=HTMLResponse)
async def get_wan_cards(request: Request):
    """Get WAN interface cards as HTML"""
    try:
        data = get_interfaces_data()
        # Render template and get body
        template = templates.get_template("partials/wan_cards.html")
        rendered = template.render({
            "request": request,
            "wan": data["wan"]
        })
        # Strip leading/trailing whitespace
        rendered = rendered.strip()
        return HTMLResponse(content=rendered)
    except Exception as e:
        logging.error(f"Error in get_wan_cards: {e}", exc_info=True)
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/interfaces/lan", response_class=HTMLResponse)
async def get_lan_cards(request: Request):
    """Get LAN interface cards as HTML"""
    try:
        data = get_interfaces_data()
        # Render template and get body
        template = templates.get_template("partials/lan_cards.html")
        rendered = template.render({
            "request": request,
            "lan": data["lan"]
        })
        # Strip leading/trailing whitespace
        rendered = rendered.strip()
        return HTMLResponse(content=rendered)
    except Exception as e:
        logging.error(f"Error in get_lan_cards: {e}", exc_info=True)
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/interfaces/other", response_class=HTMLResponse)
async def get_other_cards(request: Request):
    """Get Other interface cards as HTML"""
    try:
        data = get_interfaces_data()
        # Render template and get body
        template = templates.get_template("partials/other_cards.html")
        rendered = template.render({
            "request": request,
            "other": data["other"]
        })
        # Strip leading/trailing whitespace
        rendered = rendered.strip()
        return HTMLResponse(content=rendered)
    except Exception as e:
        logging.error(f"Error in get_other_cards: {e}", exc_info=True)
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/interfaces/wan-info", response_class=HTMLResponse)
async def get_wan_info(request: Request):
    """Get WAN info (CSS class data attribute)"""
    try:
        data = get_interfaces_data()
        wan_active = get_wan_active_status(data)
        # Return only the data attribute, not the whole card
        info_html = f"<div data-wan-status='{'active' if wan_active else 'inactive'}' class='{'wan-active' if wan_active else 'wan-inactive'}'></div>"
        # Update the card's class using hx-swap-oob (only update class, not replace entire card)
        wan_class = 'wan-active' if wan_active else 'wan-inactive'
        # Use a script to update the class attribute instead of replacing the entire card
        card_html = f"<script>document.getElementById('wan-card').className = 'card {wan_class}';</script>"
        return HTMLResponse(content=info_html + card_html)
    except Exception as e:
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/interfaces/lan-info", response_class=HTMLResponse)
async def get_lan_info(request: Request):
    """Get LAN info (IP addresses and CSS class)"""
    try:
        data = get_interfaces_data()
        lan_info = extract_lan_info(data)
        # Return hidden container with data + hx-swap-oob elements for updating card and IP spans
        info_html = templates.TemplateResponse("partials/lan_info.html", {
            "request": request,
            **lan_info
        })
        # Update the card's class using hx-swap-oob (only update class, not replace entire card)
        card_class = "lan-active" if lan_info.get("lan_active") else "lan-inactive"
        # Use a script to update the class attribute instead of replacing the entire card
        card_html = f"<script>document.getElementById('lan-card').className = 'card {card_class}';</script>"
        # Update IP spans using hx-swap-oob
        ipv4_content = lan_info.get('lan_ipv4', 'N/A')
        if lan_info.get('lan_ipv4active') is not None:
            ipv4_class = 'ipv4-active' if lan_info.get('lan_ipv4active') else 'ipv4-inactive'
            ipv4_status = '✓ Active' if lan_info.get('lan_ipv4active') else '✗ Inactive'
            ipv4_content += f' <span class="{ipv4_class}">({ipv4_status})</span>'
        ipv4_html = f"<span id='lan-ipv4' hx-swap-oob='outerHTML'>{ipv4_content}</span>"
        
        ipv6_content = lan_info.get('lan_ipv6', 'N/A')
        if lan_info.get('lan_ipv6active') is not None:
            ipv6_class = 'ipv6-active' if lan_info.get('lan_ipv6active') else 'ipv6-inactive'
            ipv6_status = '✓ Active' if lan_info.get('lan_ipv6active') else '✗ Inactive'
            ipv6_content += f' <span class="{ipv6_class}">({ipv6_status})</span>'
        ipv6_html = f"<span id='lan-ipv6' hx-swap-oob='outerHTML'>{ipv6_content}</span>"
        
        return HTMLResponse(content=info_html.body.decode() + card_html + ipv4_html + ipv6_html)
    except Exception as e:
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)


@router.post("/interfaces/activate", response_class=HTMLResponse)
async def activate_interface(request: Request, interface: str = Form(...)):
    """Activate interface by doing down/up cycle"""
    try:
        interface_name = interface.strip()
        
        if not interface_name:
            error_html = "<div class='error'>Missing interface parameter</div>"
            return HTMLResponse(content=error_html, status_code=400)
        
        # Validate interface
        if interface_name not in allowed_interfaces:
            error_html = f"<div class='error'>Interface {interface_name} is not allowed</div>"
            return HTMLResponse(content=error_html, status_code=400)
        
        # Read current LAN interfaces from env file
        if os.path.exists(LAN_ENV_FILE):
            with open(LAN_ENV_FILE) as f:
                current_lan_interfaces = set(f.read().strip().split("\n"))
        else:
            current_lan_interfaces = {"wlan0"}

        if interface_name in current_lan_interfaces:
            error_html = f"<div class='error'>Cannot activate LAN interface {interface_name}</div>"
            return HTMLResponse(content=error_html, status_code=400)
        
        # Check if interface exists and is up
        ifaces = ifaces_get()
        if interface_name not in ifaces:
            error_html = f"<div class='error'>Interface {interface_name} not found</div>"
            return HTMLResponse(content=error_html, status_code=404)
        
        if ifaces[interface_name].get("state") != "up":
            error_html = f"<div class='error'>Interface {interface_name} is not up</div>"
            return HTMLResponse(content=error_html, status_code=400)
        
        # Activate interface
        logging.debug(f"Activating interface {interface_name}")
        if_downup(interface_name)
        
        # Get updated data
        interfaces_data = get_interfaces_data()
        
        # Render all templates with hx-swap-oob
        wan_template = templates.get_template("partials/wan_cards.html")
        wan_html = wan_template.render({
            "request": request,
            "wan": interfaces_data["wan"]
        }).strip()
        
        lan_template = templates.get_template("partials/lan_cards.html")
        lan_html = lan_template.render({
            "request": request,
            "lan": interfaces_data["lan"]
        }).strip()
        
        other_template = templates.get_template("partials/other_cards.html")
        other_html = other_template.render({
            "request": request,
            "other": interfaces_data["other"]
        }).strip()
        
        # WAN info
        wan_active = get_wan_active_status(interfaces_data)
        wan_class = 'wan-active' if wan_active else 'wan-inactive'
        wan_info_html = f"<script>document.getElementById('wan-card').className = 'card {wan_class}';</script>"
        
        # LAN info
        lan_info = extract_lan_info(interfaces_data)
        lan_info_template = templates.get_template("partials/lan_info.html")
        lan_info_html = lan_info_template.render({
            "request": request,
            **lan_info
        }).strip()
        
        card_class = "lan-active" if lan_info.get("lan_active") else "lan-inactive"
        lan_card_html = f"<script>document.getElementById('lan-card').className = 'card {card_class}';</script>"
        
        ipv4_content = lan_info.get('lan_ipv4', 'N/A')
        if lan_info.get('lan_ipv4active') is not None:
            ipv4_class = 'ipv4-active' if lan_info.get('lan_ipv4active') else 'ipv4-inactive'
            ipv4_status = '✓ Active' if lan_info.get('lan_ipv4active') else '✗ Inactive'
            ipv4_content += f' <span class="{ipv4_class}">({ipv4_status})</span>'
        ipv4_html = f"<span id='lan-ipv4' hx-swap-oob='outerHTML'>{ipv4_content}</span>"
        
        ipv6_content = lan_info.get('lan_ipv6', 'N/A')
        if lan_info.get('lan_ipv6active') is not None:
            ipv6_class = 'ipv6-active' if lan_info.get('lan_ipv6active') else 'ipv6-inactive'
            ipv6_status = '✓ Active' if lan_info.get('lan_ipv6active') else '✗ Inactive'
            ipv6_content += f' <span class="{ipv6_class}">({ipv6_status})</span>'
        ipv6_html = f"<span id='lan-ipv6' hx-swap-oob='outerHTML'>{ipv6_content}</span>"

        # Combine all with hx-swap-oob
        response_html = (
            f'<div id="wan-interfaces-container" hx-swap-oob="innerHTML">{wan_html}</div>'
            f'<div id="lan-interfaces-container" hx-swap-oob="innerHTML">{lan_html}</div>'
            f'<div id="other-interfaces-container" hx-swap-oob="innerHTML">{other_html}</div>'
            f'{wan_info_html}'
            f'{lan_info_html}'
            f'{lan_card_html}'
            f'{ipv4_html}'
            f'{ipv6_html}'
        )

        # Return response with 200 status for success message
        response = HTMLResponse(content=response_html, status_code=200)
        response.headers["HX-Trigger"] = "refreshStatus"
        return response

    except Exception as e:
        logging.error(f"Error in activate_interface: {e}", exc_info=True)
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)


@router.post("/interfaces/move", response_class=HTMLResponse)
async def move_interface(request: Request, interface: str = Form(...), target: str = Form(...)):
    """Move interface between LAN and Other, update env file and return updated HTML"""
    try:
        interface_name = interface.strip()
        target_name = target.strip().lower()

        # Validate target
        if target_name not in ["lan", "other"]:
            error_html = "<div class='error'>Invalid target - must be 'lan' or 'other'</div>"
            return HTMLResponse(content=error_html, status_code=400)

        # Validate interface
        if interface_name not in allowed_interfaces:
            error_html = f"<div class='error'>Interface {interface_name} is not allowed</div>"
            return HTMLResponse(content=error_html, status_code=400)

        # Read current LAN interfaces
        if os.path.exists(LAN_ENV_FILE):
            with open(LAN_ENV_FILE) as f:
                current_lan = set(line.strip() for line in f.read().strip().split("\n") if line.strip())
        else:
            current_lan = {"wlan0"}

        # Validate that we're not removing the last LAN interface
        if target_name == "other" and interface_name in current_lan and len(current_lan) <= 1:
            error_html = "<div class='error'>Cannot remove the last LAN interface. At least one LAN interface must remain.</div>"
            return HTMLResponse(content=error_html, status_code=400)

        # Update LAN interfaces based on target
        if target_name == "lan":
            current_lan.add(interface_name)
        elif target_name == "other":
            current_lan.discard(interface_name)

        # Write back to file
        os.makedirs(os.path.dirname(LAN_ENV_FILE), exist_ok=True)
        with open(LAN_ENV_FILE, 'w') as f:
            for iface in sorted(current_lan):
                f.write(f"{iface}\n")

        # Get updated data
        interfaces_data = get_interfaces_data()

        # Render all templates with hx-swap-oob
        wan_template = templates.get_template("partials/wan_cards.html")
        wan_html = wan_template.render({
            "request": request,
            "wan": interfaces_data["wan"]
        }).strip()

        lan_template = templates.get_template("partials/lan_cards.html")
        lan_html = lan_template.render({
            "request": request,
            "lan": interfaces_data["lan"]
        }).strip()

        other_template = templates.get_template("partials/other_cards.html")
        other_html = other_template.render({
            "request": request,
            "other": interfaces_data["other"]
        }).strip()

        # WAN info
        wan_active = get_wan_active_status(interfaces_data)
        wan_class = 'wan-active' if wan_active else 'wan-inactive'
        wan_info_html = f"<script>document.getElementById('wan-card').className = 'card {wan_class}';</script>"

        # LAN info
        lan_info = extract_lan_info(interfaces_data)
        lan_info_template = templates.get_template("partials/lan_info.html")
        lan_info_html = lan_info_template.render({
            "request": request,
            **lan_info
        }).strip()

        card_class = "lan-active" if lan_info.get("lan_active") else "lan-inactive"
        lan_card_html = f"<script>document.getElementById('lan-card').className = 'card {card_class}';</script>"

        ipv4_content = lan_info.get('lan_ipv4', 'N/A')
        if lan_info.get('lan_ipv4active') is not None:
            ipv4_class = 'ipv4-active' if lan_info.get('lan_ipv4active') else 'ipv4-inactive'
            ipv4_status = '✓ Active' if lan_info.get('lan_ipv4active') else '✗ Inactive'
            ipv4_content += f' <span class="{ipv4_class}">({ipv4_status})</span>'
        ipv4_html = f"<span id='lan-ipv4' hx-swap-oob='outerHTML'>{ipv4_content}</span>"

        ipv6_content = lan_info.get('lan_ipv6', 'N/A')
        if lan_info.get('lan_ipv6active') is not None:
            ipv6_class = 'ipv6-active' if lan_info.get('lan_ipv6active') else 'ipv6-inactive'
            ipv6_status = '✓ Active' if lan_info.get('lan_ipv6active') else '✗ Inactive'
            ipv6_content += f' <span class="{ipv6_class}">({ipv6_status})</span>'
        ipv6_html = f"<span id='lan-ipv6' hx-swap-oob='outerHTML'>{ipv6_content}</span>"

        # Combine all with hx-swap-oob
        response_html = (
            f'<div id="wan-interfaces-container" hx-swap-oob="innerHTML">{wan_html}</div>'
            f'<div id="lan-interfaces-container" hx-swap-oob="innerHTML">{lan_html}</div>'
            f'<div id="other-interfaces-container" hx-swap-oob="innerHTML">{other_html}</div>'
            f'{wan_info_html}'
            f'{lan_info_html}'
            f'{lan_card_html}'
            f'{ipv4_html}'
            f'{ipv6_html}'
        )

        # Return response with 200 status for success message
        response = HTMLResponse(content=response_html, status_code=200)
        response.headers["HX-Trigger"] = "refreshStatus"
        return response

    except Exception as e:
        logging.error(f"Error in move_interface: {e}", exc_info=True)
        error_html = f"<div class='error'>Error: {str(e)}</div>"
        return HTMLResponse(content=error_html, status_code=500)

