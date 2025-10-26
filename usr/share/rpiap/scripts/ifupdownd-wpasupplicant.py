#!/usr/bin/env python3

import os
import sys
import logging


# settings
LAN_ENV="/var/lib/rpiap/env/lan"
WPASUPPLICANT_CONF="/etc/rpiap/wpasupplicant"


def lan_interfaces() -> [str]:
    """
    """

    if not os.path.exists(LAN_ENV):
        return "wlan0" # XXX: backward compatibility

    with open(LAN_ENV, "r") as f:
        return f.read().strip().split("\n")


def wpasupplicant_up(interface: str) -> bool:
    """
    """

    if not os.path.exists(f"{WPASUPPLICANT_CONF}/{interface}.conf"):
        return False

    control=f"/etc/service/rpiap_wpasupplicant_{interface}/supervise/control"
    if not os.path.exists(control):
        return False

    with open(control, "w") as f:
        f.write("tu")

    return True

def wpasupplicant_down(interface: str) -> bool:
    """
    """

    if not os.path.exists(f"{WPASUPPLICANT_CONF}/{interface}.conf"):
        return False

    control=f"/etc/service/rpiap_wpasupplicant_{interface}/supervise/control"
    if not os.path.exists(control):
        return False

    with open(control, "w") as f:
        f.write("d")

    return True


if __name__ == "__main__":

    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.INFO)

    # interface
    interface=sys.argv[1]
    logging.debug(f"interface = '{interface}'")

    # phase
    phase=sys.argv[2]
    logging.debug(f"phase = '{phase}'")

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
            if interface not in laninterfaces:
                if wpasupplicant_up(interface):
                    log(f"running wpasupplicant on {interface}")
        case "down":
            if interface not in laninterfaces:
                if wpasupplicant_down(interface):
                    log(f"stoping wpasupplicant on {interface}")
        case _:
            pass

sys.exit(0)
