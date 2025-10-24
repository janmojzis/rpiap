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
        # use trick how to get local IP - try external connection first
        local_ip = None
        try:
            s.connect(("1.1.1.1", 53))
            local_ip = s.getsockname()[0]
        except (OSError, socket.error):
            # If it fails (no internet connection)
            local_ip = None

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
                    if local_ip and addr.address == local_ip:
                        ret[ifname]["active"] = True
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

    # WAN
    wan = []
    for ifname in ifaces:
        if ifname in ["eth0", "eth1", "wlan1", "usb0"]:
            wan.append(ifaces[ifname])

    response = {
        "success": True,
        "wan": wan,
        "lan": lan
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
        
        # Check if interface is up
        if interface_found["state"] != "up":
            return {
                "success": False,
                "error": f"Cannot switch to {interface_name} - interface is down"
            }
        
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
