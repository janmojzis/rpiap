#!/bin/sh

interface=$1
phase=$2

case "${phase}" in

  up)
    /sbin/ifup "${interface}"
  ;;

  down)
    /sbin/ifdown "${interface}"
  ;;

  *)
    exit 1
  ;;
esac

exit 0
