#!/bin/sh
set -e

script=$0
interface=$1
phase=$2
bkiface=$3

mkdir -p /var/lib/rpiap/service/udhcpc/env

case "${phase}" in

  up)
    echo "${interface}" > /var/lib/rpiap/service/udhcpc/env/IFACE
    svc -tu /etc/service/rpiap_udhcpc
    echo "${script}: ${interface}: phase=${phase}, running udhcpc on ${interface}" >&2
  ;;

  down)
    if [ x"${bkiface}" != x ]; then
      echo "${script}: ${interface}: phase=${phase}, falling back to ${bkiface} and running udhcpc on ${bkiface}" >&2
      echo "${bkiface}" > /var/lib/rpiap/service/udhcpc/env/IFACE
      svc -t /etc/service/rpiap_udhcpc
    else
      echo "${script}: ${interface}: phase=${phase}, other interfaces are not active, stoping udhcpc" >&2
      rm /var/lib/rpiap/service/udhcpc/env/IFACE
      svc -d /etc/service/rpiap_udhcpc
    fi
  ;;

  *)
    echo "${script}: unknown phase=\"${phase}\"" >&2
    exit 1
  ;;
esac

exit 0
