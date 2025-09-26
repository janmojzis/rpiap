#!/bin/sh
set -e

echo "=== ${interface} $1 ==="

if [ x"$1" = xdeconfig ]; then
  busybox ip link set "${interface}" up
  busybox ip -4 addr flush dev "${interface}"
  busybox ip -4 route flush dev "${interface}"

  # remove dns
  rm -f '/var/lib/rpiap/service/udhcpc/var/@' || :
  svc -t /etc/service/rpiap_dqcache
fi

if [ x"$1" = xbound ] || [ x"$1" = xrenew ]; then
  busybox ifconfig $interface ${mtu:+mtu $mtu} $ip netmask $subnet ${broadcast:+broadcast $broadcast}

  oldrouter=`busybox ip -4 route show dev "${interface}" | busybox awk '$1 == "default" { print $3; }'`
  router="${router%% *}" # linux kernel supports only one (default) route

  if [ "x${router}" != "x${oldrouter}" ]; then
    busybox ip -4 route flush default
    busybox ip -4 route add default via "${router}" dev "${interface}"
  fi

  # update dns
  for ns in ${dns}; do
    echo "${ns}"
  done > '/var/lib/rpiap/service/udhcpc/var/@'
  svc -t /etc/service/rpiap_dqcache

  echo "IP=$ip/$subnet router=$router domain=\"$domain\" dns=\"$dns\" lease=$lease" >&2
fi
