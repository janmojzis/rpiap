#!/bin/sh

ifname=$1
phase=$2
basename="`basename $0`"

if ! grep -Fxq -- "${ifname}" /var/lib/rpiap/env/lan; then
  iftype=WAN
else
  iftype=LAN
fi

log() {
  text=$1
  echo "${basename}: INFO: ${iftype} ${ifname}: ${phase}: ${text}"
}

if [ x"${ifname}" != xwlan0 ]; then
  # currently only wlan0 supported
  exit 0
fi

if ! grep -Fxq -- "${ifname}" /var/lib/rpiap/env/lan; then
  # ifname is not in LAN configuration
  exit 0
fi

case "${phase}" in
  up)
    svc -u /etc/service/rpiap_hostapd
    log "running hostapd on ${ifname}"
  ;;

  down)
    svc -d /etc/service/rpiap_hostapd
    log "stopping hostapd on ${ifname}"
  ;;

  *)
    # nothing to do
    exit 0
  ;;
esac

exit 0
