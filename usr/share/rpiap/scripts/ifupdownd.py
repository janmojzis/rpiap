#!/usr/bin/python3

import os
import socket
import struct
import select
import logging
import argparse
import subprocess

RTM_NEWLINK = 16
RTM_DELLINK = 17

# Netlink constants
NETLINK_ROUTE = 0
RTMGRP_LINK = 1

# Flags from ifinfomsg
IFF_UP = 0x1
IFF_BROADCAST = 0x2
IFF_DEBUG = 0x4
IFF_LOOPBACK = 0x8
IFF_POINTOPOINT = 0x10
IFF_NOTRAILERS = 0x20
IFF_RUNNING = 0x40
IFF_NOARP = 0x80
IFF_PROMISC = 0x100

IFF_MULTICAST = 1<<12
IFF_LOWER_UP = 1<<16
IFF_DORMANT = 1<<17
IFF_ECHO = 1<<18

# Attribute types (from linux/if_link.h)
IFLA_IFNAME = 3

def rtattr_parse(data):
    """Parse TLV-encoded Netlink attributes."""
    attrs = {}
    while len(data) >= 4:
        rta_len, rta_type = struct.unpack("HH", data[:4])
        attr_data = data[4:rta_len]
        attrs[rta_type] = attr_data.rstrip(b'\x00')
        # Align to 4 bytes
        rta_len = (rta_len + 3) & ~3
        data = data[rta_len:]
    return attrs

def netlink_parse(data: bytes) -> None:

    if 1==1:

        # Parse Netlink message header
        while len(data) >= 16:
            nlmsg_len, nlmsg_type, nlmsg_flags, nlmsg_seq, nlmsg_pid = struct.unpack("IHHII", data[:16])
            msg = data[16:nlmsg_len]

            # RTM_NEWLINK or RTM_DELLINK
            if nlmsg_type in (RTM_NEWLINK, RTM_DELLINK):
                # struct ifinfomsg { unsigned char family; unsigned char pad;
                #                    unsigned short type; int index;
                #                    unsigned int flags; unsigned int change; };
                if len(msg) < 16:
                    if len(msg) > 0:
                        logging.warning(f"len(msg) < 16")
                    break
                family, _, if_type, if_index, flags, change = struct.unpack("=BBHiII", msg[:16])
                attrs = rtattr_parse(msg[16:])

                name = attrs.get(IFLA_IFNAME, b'?').decode()
                state = ""
                if bool(flags & IFF_UP):
                    state += "IFF_UP,"
                    flags -= IFF_UP
                if bool(flags & IFF_BROADCAST):
                    state += "IFF_BROADCAST,"
                    flags -= IFF_BROADCAST
                if bool(flags & IFF_LOOPBACK):
                    state += "IFF_LOOPBACK,"
                    flags -= IFF_LOOPBACK
                if bool(flags & IFF_DEBUG):
                    state += "IFF_DEBUG,"
                    flags -= IFF_DEBUG
                if bool(flags & IFF_POINTOPOINT):
                    state += "IFF_POINTOPOINT,"
                    flags -= IFF_POINTOPOINT
                if bool(flags & IFF_NOTRAILERS):
                    state += "IFF_NOTRAILERS,"
                    flags -= IFF_NOTRAILERS
                if bool(flags & IFF_RUNNING):
                    state += "IFF_RUNNING,"
                    flags -= IFF_RUNNING
                if bool(flags & IFF_NOARP):
                    state += "IFF_NOARP,"
                    flags -= IFF_NOARP
                if bool(flags & IFF_PROMISC):
                    state += "IFF_PROMISC,"
                    flags -= IFF_PROMISC
                if bool(flags & IFF_MULTICAST):
                    state += "IFF_MULTICAST,"
                    flags -= IFF_MULTICAST
                if bool(flags & IFF_LOWER_UP):
                    state += "IFF_LOWER_UP,"
                    flags -= IFF_LOWER_UP
                if bool(flags & IFF_DORMANT):
                    state += "IFF_DORMANT,"
                    flags -= IFF_DORMANT
                if len(state) > 0:
                    state = state[0:-1]
                if flags == 0:
                    logging.debug(f"{name}: {state}")
                else:
                    logging.debug(f"{name}: {state}, otherflags = {flags}")
            else:
                logging.warning(f"unknown nlmsg_type: {nlmsg_type}")

            # Move to next message
            nlmsg_len = (nlmsg_len + 3) & ~3
            data = data[nlmsg_len:]



def iflist(allowed = []):
    '''
    '''

    ret = {}
    for iface in allowed:
        try:
            link = open(f'/sys/class/net/{iface}/operstate').read().strip()
            device = 'up'
        except FileNotFoundError:
            link = 'down'
            device = 'down'
        ret[iface] = {}
        ret[iface]['link'] = link
        ret[iface]['device'] = device

    logging.debug('interfaces = %s' % (ret))
    return ret


def scripts_get(directory: str) -> [str]:
    """
    """

    result = []
    for filename in os.listdir(directory):
        result.append(f"{directory}/{filename}")
    result.sort()
    return result



parser = argparse.ArgumentParser(description='ifupdown.py')
parser.add_argument('-v', '--verbose',
                        action='count',
                        help='verbosity',
                        default=0)

parser.add_argument('-i', '--interface',
                        action='append',
                        help='interface')

parser.add_argument('-d', '--device',
                        action='store',
                        help='direcrtory containing device up/down scripts')

parser.add_argument('-l', '--link',
                        action='store',
                        help='direcrtory containing link up/down scripts')


args = parser.parse_args()


# verbosity
LOG_LEVELS = ["INFO", "DEBUG"]
if (args.verbose > len(LOG_LEVELS) - 1):
    args.verbose = len(LOG_LEVELS) - 1

logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=LOG_LEVELS[args.verbose])
logging.debug('start')

# bind netlink interface
s = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, NETLINK_ROUTE)
s.bind((0, RTMGRP_LINK))

# old dictionary
old = {}

# allowed interfaces
allowed = args.interface
if allowed is None:
    parser.error("parameter -i/--interface is required")
logging.debug(f'allowed interfaces: {allowed}')
for iface in allowed:
    old[iface] = {}
    old[iface]['link'] = 'none'
    old[iface]['device'] = 'none'

# scripts
linkscripts = scripts_get(args.link)
devicescripts = scripts_get(args.device)


while True:
    try:
        current = iflist(allowed)

        active = []
        for iface in allowed:
            if current[iface]['link'] == 'up':
                active.append(iface)

        for iface in allowed:
            # bridge
            if os.path.exists(f"/sys/class/net/{iface}/brif"):
                logging.debug(f'{iface}: is bridge, nothing to do')
                continue
            # lan bridge
            if os.path.exists(f"/sys/class/net/lan/brif/{iface}"):
                logging.debug(f'{iface}: is assigned to lan bridge, nothing to do')
                continue
            # link
            if old[iface]['link'] != current[iface]['link']:
                for script in linkscripts:
                    cmd = [script, iface, current[iface]['link']] + active
                    if old[iface]['link'] == 'none' and current[iface]['link'] != 'up':
                        logging.debug(f'{iface}: {old[iface]["link"]} -> {current[iface]["link"]}, nothing to do')
                    else:
                        logging.debug(f'{iface}: {old[iface]["link"]} -> {current[iface]["link"]}, running {cmd}')
                        subprocess.run(cmd)

                old[iface]['link'] = current[iface]['link']

            # device
            if old[iface]['device'] != current[iface]['device']:
                for script in devicescripts:
                    cmd = [script, iface, current[iface]['device']]
                    logging.debug(f'{iface}: {old[iface]["device"]} -> {current[iface]["device"]}, running {cmd}')
                    subprocess.run(cmd)

                old[iface]['device'] = current[iface]['device']

    except Exception as e:
        logging.fatal('%s' % (e))

    # wait for netlink event
    r, _, _ = select.select([s], [], [])
    if len(r) > 0:
        logging.debug('netlink event')
        data = s.recv(65535)
        netlink_parse(data)

exit(0)
