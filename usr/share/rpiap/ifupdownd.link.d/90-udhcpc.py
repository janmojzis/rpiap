#!/usr/bin/env python3

import os
import sys
import logging


# settings
UDHCPC_ENV="/var/lib/rpiap/service/udhcpc/env/IFACE"
UDHCPC_CONTROL="/var/lib/rpiap/service/udhcpc/supervise/control"
LAN_ENV="/var/lib/rpiap/env/lan"


def lan_interfaces() -> [str]:
    """
    """

    with open(LAN_ENV, "r") as f:
        return f.read().strip().split("\n")

def udhcpc_interface() -> str:
    """
    """

    if not os.path.exists(UDHCPC_ENV):
        return ""

    with open(UDHCPC_ENV, "r") as f:
        return f.read().strip()

def udhcpc_up(interface: str) -> None:
    """
    """

    dirname=os.path.dirname(UDHCPC_ENV)
    os.makedirs(dirname, exist_ok=True)

    with open(UDHCPC_ENV, "w") as f:
        f.write(interface)

    with open(UDHCPC_CONTROL, "w") as f:
        f.write("tu")


def udhcpc_down() -> None:
    """
    """

    if os.path.exists(UDHCPC_ENV):
        os.unlink(UDHCPC_ENV)

    with open(UDHCPC_CONTROL, "w") as f:
        f.write("d")


if __name__ == "__main__":

    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.INFO)

    # interface
    interface=sys.argv[1]
    logging.debug(f"interface = '{interface}'")

    # phase
    phase=sys.argv[2]
    logging.debug(f"phase = '{phase}'")

    # all backup interfaces
    bkinterfaces=sys.argv[3:]
    logging.debug(f"all bkinterfaces = {bkinterfaces}")

    # LAN interfaces
    laninterfaces=lan_interfaces()
    logging.debug(f"laninterfaces = {laninterfaces}")

    # WAN backup interfaces
    bkinterfaces = [iface for iface in bkinterfaces if iface not in laninterfaces]
    logging.debug(f"wan bkinterfaces = {bkinterfaces}")

    # WAN active interface
    activeinterface = udhcpc_interface()
    logging.debug(f"wan activeinterface = {activeinterface}")

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
                udhcpc_up(interface)
                log(f"running udhcpc on {interface}")
            else:
                log()
        case "down":
            if interface not in laninterfaces:
                if len(bkinterfaces) == 0:
                    udhcpc_down()
                    log("other interfaces are not active, stopping udhcpc")
                else:
                    if interface == activeinterface:
                        bkiface = bkinterfaces[0]
                        udhcpc_up(bkiface)
                        log(f"falling back to {bkiface}, and running udhcpc on {bkiface}")
                    else:
                        log(f"interface not active, nothing to do")
            else:
                log()
        case _:
            log()

sys.exit(0)
