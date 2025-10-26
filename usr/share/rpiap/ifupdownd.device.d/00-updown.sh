#!/bin/sh
set -e

script=$0
interface=$1
phase=$2

case "${phase}" in

  up)
    echo "${script}: ${interface}: phase=${phase}, executing /sbin/ifup ${interface}" >&2
    /sbin/ifup "${interface}"
  ;;

  down)
    echo "${script}: ${interface}: phase=${phase}, executing /sbin/ifdown ${interface}" >&2
    /sbin/ifdown "${interface}"
  ;;

  *)
    echo "${script}: unknown phase=\"${phase}\"" >&2
    exit 1
  ;;
esac

exit 0
