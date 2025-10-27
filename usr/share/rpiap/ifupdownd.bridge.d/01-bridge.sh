#!/bin/sh

interface=$1
phase=$2

if [ x"${interface}" != 'xlan' ]; then
  exit 1
fi

case "${phase}" in

  up)
    for name in `cat /var/lib/rpiap/env/lan`; do
      busybox ip link set "${name}" master 'lan'
    done
  ;;

  down)
    for name in `cat /var/lib/rpiap/env/lan`; do
      busybox ip link set "${name}" nomaster
    done
  ;;

  *)
    exit 1
  ;;
esac

exit 0
