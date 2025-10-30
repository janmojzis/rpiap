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

if [ x"${iftype}" != xWAN ]; then
  exit 0
fi

case "${phase}" in
  up)
    echo 2 > "/proc/sys/net/ipv6/conf/${ifname}/accept_ra"
    echo 1 > "/proc/sys/net/ipv6/conf/${ifname}/autoconf"
    log "IPv6 autoconf enabled on ${ifname} (accept_ra = 2, autoconf = 1)"
  ;;

  down)
    if [ -e "/proc/sys/net/ipv6/conf/${ifname}/accept_ra" ] && [ -e "/proc/sys/net/ipv6/conf/${ifname}/autoconf" ] ; then
      echo 0 > "/proc/sys/net/ipv6/conf/${ifname}/accept_ra"
      echo 0 > "/proc/sys/net/ipv6/conf/${ifname}/autoconf"
      log "IPv6 autoconf disabled on ${ifname} (accept_ra = 0, autoconf = 0)"
    fi
  ;;

  *)
    # nothing to do
    exit 0
  ;;
esac

exit 0
