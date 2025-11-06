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

with open("/var/lib/rpiap/env/lan") as f:
    lan_interfaces = f.read().strip().split("\n")

os.chdir("/var/lib/rpiap/empty")
os.chroot(".")

allowed_interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "usb0"]

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
            raise
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
            #ret[ifname]["active"] = False
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

def handle_get():
    """Handle GET request - return all data"""

    # ALL interfaces
    ifaces = ifaces_get()

    # LAN interfaces
    lan = ifaces["lan"]
    lan["interfaces"] = []
    lan["ipv4active"] = len(lan["ipv4"]) > 0
    lan["ipv6active"] = len(lan["ipv6"]) > 0
    for ifname in lan_interfaces:
        tmp = {}
        try:
            tmp["state"] = ifaces[ifname]["state"]
            tmp["interface"] = ifaces[ifname]["interface"]
            tmp["mac"] = ifaces[ifname]["mac"]
        except KeyError:
            # interface is down
            tmp["state"] = "down"
            tmp["interface"] = ifname
        lan["interfaces"].append(tmp)
            

    # WAN/OTHER interfaces
    wan = {}
    other = {}
    wan["interfaces"] = []
    other["interfaces"] = []
    for ifname in ifaces:
        if ifname in lan_interfaces:
            continue
        if ifname in allowed_interfaces:
            ifaces[ifname]["ipv4active"] = if_ip4_isactive(ifname)
            ifaces[ifname]["ipv6active"] = if_ip6_isactive(ifname)
            #if ifaces[ifname]["ipv6active"] or ifaces[ifname]["ipv4active"]:
            if ifaces[ifname]["ipv4active"]:
                wan["interfaces"].append(ifaces[ifname])
            else:
                other["interfaces"].append(ifaces[ifname])

    response = {
        "success": True,
        "wan": wan,
        "lan": lan,
        "other": other,
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
        flagfound = False
        for ifname in ifaces:
            if ifname in allowed_interfaces:
                if ifname not in lan_interfaces:
                    if ifname == interface_name:
                        flagfound = True

        if not flagfound:
            raise Exception(f"unable to add {interface_name} as WAN")
        
        # Update active interface
        logging.debug("Set active interface {interface_name}")
        if_downup(interface_name)
        
        # Return updated data
        return {
            "success": True,
            "message": f"Successfully switched to {interface_name}",
            "wan": [ifaces[ifname] for ifname in ifaces if ifname in ["eth0", "eth1", "wlan1", "usb0"]],
            "lan": [ifaces[ifname] for ifname in ifaces if ifname in ["wlan0"]]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing request: {str(e)}"
        }

if __name__ == "__main__":
    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.DEBUG)

    print("Content-Type: application/json\n")

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
