#!/bin/sh

ifname=$1
phase=$2
basename="`basename $0`"

if ! grep -Fxq -- "${ifname}" /var/lib/rpiap/env/lan; then
  iftype=WAN
  exit 0
else
  iftype=LAN
fi

log() {
  text=$1
  echo "${basename}: INFO: ${iftype} ${ifname}: ${phase}: ${text}"
}

if [ x"${phase}" = xup ]; then
  if busybox ip link set "${ifname}" master 'lan'; then
    log "interface ${ifname} added to bridge 'lan'"
  fi
fi

if [ x"${phase}" = xdown ]; then
  if busybox ip link set "${ifname}" nomaster; then
    log "interface ${ifname} removed from bridge"
  fi
fi

exit 0
