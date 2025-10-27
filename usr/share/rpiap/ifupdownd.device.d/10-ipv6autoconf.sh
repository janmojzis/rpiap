#!/bin/sh

interface=$1
phase=$2


# XXX: backward compatibility
if [ ! -f /var/lib/rpiap/env/lan ] && [ x"${interface}" = xwlan0 ]; then
  # LAN
  exit 0
fi

if grep -q "^${interface}"'$' /var/lib/rpiap/env/lan 2>/dev/null; then
  # LAN
  exit 0
fi

case "${phase}" in

  up)
    echo 2 > "/proc/sys/net/ipv6/conf/${interface}/accept_ra"
    echo 1 > "/proc/sys/net/ipv6/conf/${interface}/autoconf"
  ;;

  down)
    if [ -e "/proc/sys/net/ipv6/conf/${interface}/accept_ra" ]; then
      echo 0 > "/proc/sys/net/ipv6/conf/${interface}/accept_ra"
    fi
    if [ -e "/proc/sys/net/ipv6/conf/${interface}/autoconf" ]; then
      echo 0 > "/proc/sys/net/ipv6/conf/${interface}/autoconf"
    fi
  ;;

  *)
    exit 1
  ;;
esac

exit 0
