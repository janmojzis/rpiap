#!/usr/bin/python3

import time, os
import logging
import argparse
import subprocess


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



parser = argparse.ArgumentParser(description='ifupdown.py')
parser.add_argument('-v', '--verbose',
                        action='count',
                        help='verbosity',
                        default=0)

parser.add_argument('-i', '--interface',
                        action='append',
                        help='interface')

parser.add_argument('-d', '--device',
                        action='append',
                        help='device up/down script')

parser.add_argument('-l', '--link',
                        action='append',
                        help='link up/down script')

args = parser.parse_args()


# verbosity
LOG_LEVELS = ["INFO", "DEBUG"]
if (args.verbose > len(LOG_LEVELS) - 1):
    args.verbose = len(LOG_LEVELS) - 1

logging.basicConfig(level=LOG_LEVELS[args.verbose], datefmt='%Y-%m-%d %H:%M:%S')
logging.info('start')

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
linkscripts = args.link
if linkscripts is None:
    linkscripts = []

devicescripts = args.device
if devicescripts is None:
    devicescripts = []


while True:
    try:
        current = iflist(allowed)

        active = []
        for iface in allowed:
            if current[iface]['link'] == 'up':
                active.append(iface)

        for iface in allowed:
            # link
            if old[iface]['link'] != current[iface]['link']:
                for script in linkscripts:
                    cmd = [script, iface, current[iface]['link']] + active
                    if old[iface]['link'] == 'none' and current[iface]['link'] != 'up':
                        logging.info(f'{iface}: {old[iface]["link"]} -> {current[iface]["link"]}, nothing to do')
                    else:
                        logging.info(f'{iface}: {old[iface]["link"]} -> {current[iface]["link"]}, running {cmd}')
                        subprocess.run(cmd)

                    old[iface]['link'] = current[iface]['link']

            # device
            if old[iface]['device'] != current[iface]['device']:
                for script in devicescripts:
                    cmd = [script, iface, current[iface]['device']]
                    logging.info(f'{iface}: {old[iface]["device"]} -> {current[iface]["device"]}, running {cmd}')
                    subprocess.run(cmd)

                    old[iface]['device'] = current[iface]['device']

    except Exception as e:
        logging.fatal('%s' % (e))

    time.sleep(2)

exit(0)
