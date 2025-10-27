#!/bin/sh

interface=$1
phase=$2

# XXX - currently only wlan0 supported
if [ x"${interface}" != xwlan0 ]; then
  exit 0
fi

if ! grep -Fxq -- "${interface}" /var/lib/rpiap/env/lan; then
  exit 0
fi

case "${phase}" in

  up)
    svc -u /etc/service/rpiap_hostapd
  ;;

  down)
    svc -d /etc/service/rpiap_hostapd
  ;;

  *)
    exit 1
  ;;
esac

exit 0
