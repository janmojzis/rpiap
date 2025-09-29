#!/bin/sh
set -e

script=$0
interface=$1
phase=$2

case "${phase}" in

  up)
    echo "${script}: ${interface}: phase=${phase}, executing /sbin/ifup ${interface}" >&2
    /sbin/ifup "${interface}"
    if [ x"${interface}" = xwlan1 ]; then
      echo "${script}: ${interface}: phase=${phase}, running wpasupplicant on ${interface}" >&2
      svc -tu /etc/service/rpiap_wpasupplicant
    fi
  ;;

  down)
    echo "${script}: ${interface}: phase=${phase}, executing /sbin/ifdown ${interface}" >&2
    /sbin/ifdown "${interface}"
    if [ x"${interface}" = xwlan1 ]; then
      echo "${script}: ${interface}: phase=${phase}, stopping wpasupplicant on ${interface}" >&2
      svc -d /etc/service/rpiap_wpasupplicant
    fi
  ;;

  *)
    echo "${script}: unknown phase=\"${phase}\"" >&2
    exit 1
  ;;
esac

exit 0
