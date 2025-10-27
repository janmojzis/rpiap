#!/usr/bin/env python3

# XXX - hardcoded wlan0

import os
import sys
import logging


# settings
LAN_ENV="/var/lib/rpiap/env/lan"
HOSTAPD_CONTROL="/etc/service/rpiap_hostapd/supervise/control"


def lan_interfaces() -> [str]:
    """
    """

    with open(LAN_ENV, "r") as f:
        return f.read().strip().split("\n")


def hostapd_up(interface: str) -> None:
    """
    """

    with open(HOSTAPD_CONTROL, "w") as f:
        f.write("u")

def hostapd_down(interface: str) -> None:
    """
    """

    with open(HOSTAPD_CONTROL, "w") as f:
        f.write("d")


if __name__ == "__main__":

    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.INFO)

    # interface
    interface=sys.argv[1]
    logging.debug(f"interface = '{interface}'")

    # phase
    phase=sys.argv[2]
    logging.debug(f"phase = '{phase}'")

    # LAN interfaces
    laninterfaces=lan_interfaces()
    logging.debug(f"laninterfaces = {laninterfaces}")

    # interface type LAN/WAN
    if interface not in laninterfaces:
        interfacetype = "WAN"
    else:
        interfacetype = "LAN"

    # log function
    def log(text: str | None = None) -> None:
        if text is None:
            text = "nothing to do"
        logging.info(f"{interfacetype} {interface}: {phase}: {text}")

    # main part
    match phase:
        case "up":
            if interface == "wlan0" and interface in laninterfaces:
                hostapd_up(interface)
                log(f"running hostapd on {interface}")
        case "down":
            if interface == "wlan0" and interface in laninterfaces:
                hostapd_down(interface)
                log(f"stopping hostapd on {interface}")
        case _:
            pass

sys.exit(0)
