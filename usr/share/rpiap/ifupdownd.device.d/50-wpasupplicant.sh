#!/bin/sh

ifname=$1
phase=$2
basename="`basename $0`"

if grep -Fxq -- "${ifname}" /var/lib/rpiap/env/lan; then
  iftype=LAN
  exit 0
else
  iftype=WAN
fi

log() {
  text=$1
  echo "${basename}: INFO: ${iftype} ${ifname}: ${phase}: ${text}"
}

if [ ! -h "/etc/service/rpiap_wpasupplicant_${ifname}" ]; then
  # wpasupplicant service for the ifname doesn't exist
  exit 0
fi

case "${phase}" in
  up)
    svc -u "/etc/service/rpiap_wpasupplicant_${ifname}"
    log "running wpasupplicant on ${ifname}"
  ;;

  down)
    svc -d "/etc/service/rpiap_wpasupplicant_${ifname}"
    log "stopping wpasupplicant on ${ifname}"
  ;;

  *)
    # nothing to do
    exit 0
  ;;
esac

exit 0
