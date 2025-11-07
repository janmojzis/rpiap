#!/usr/bin/env python3
import os
import psutil
import socket
import ipaddress
import struct
import fcntl

# Load LAN interfaces from env file
LAN_ENV_FILE = "/var/lib/rpiap/env/lan"
if os.path.exists(LAN_ENV_FILE):
    with open(LAN_ENV_FILE) as f:
        lan_interfaces = f.read().strip().split("\n")
else:
    lan_interfaces = ["wlan0"]

allowed_interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "usb0"]

SIOCGIFFLAGS = 0x8913  # get flags
IFF_UP = 0x1
IFF_RUNNING = 0x40


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
    for ifname in ifaces:
        if ifname in lan_interfaces or ifname == "lan":
            continue
        if ifname in allowed_interfaces:
            ifaces[ifname]["ipv4active"] = if_ip4_isactive(ifname)
            ifaces[ifname]["ipv6active"] = if_ip6_isactive(ifname)
            ifaces[ifname]["active"] = ifaces[ifname]["ipv6active"] or ifaces[ifname]["ipv4active"]
            if ifaces[ifname]["ipv6active"] or ifaces[ifname]["ipv4active"]:
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

