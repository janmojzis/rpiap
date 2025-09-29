#!/bin/sh
set -e

script=$0
interface=$1
phase=$2

case "${phase}" in

  up)
    echo "${script}: ${interface}: phase=${phase}, executing /sbin/ifup ${interface}" >&2
    /sbin/ifup "${interface}"
    if [ -h "/etc/service/rpiap_wpasupplicant_${interface}" ] && [ -f "/etc/rpiap/wpasupplicant/${interface}.conf" ]; then
      echo "${script}: ${interface}: phase=${phase}, running wpasupplicant on ${interface}" >&2
      svc -tu "/etc/service/rpiap_wpasupplicant_${interface}"
    fi
  ;;

  down)
    echo "${script}: ${interface}: phase=${phase}, executing /sbin/ifdown ${interface}" >&2
    /sbin/ifdown "${interface}"
    if [ -h "/etc/service/rpiap_wpasupplicant_${interface}" ] && [ -f "/etc/rpiap/wpasupplicant/${interface}.conf" ]; then
      echo "${script}: ${interface}: phase=${phase}, stopping wpasupplicant on ${interface}" >&2
      svc -d "/etc/service/rpiap_wpasupplicant_${interface}"
    fi
  ;;

  *)
    echo "${script}: unknown phase=\"${phase}\"" >&2
    exit 1
  ;;
esac

exit 0
