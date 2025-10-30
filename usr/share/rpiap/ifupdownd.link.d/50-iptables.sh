#!/bin/sh

ifname=$1
phase=$2
lan='lan'

if grep -Fxq -- "${ifname}" /var/lib/rpiap/env/lan; then
  exit 0
fi

if [ x"${phase}" = xup ]; then
  # IPv4 FORWARD/NAT
  if ! iptables -t nat -C POSTROUTING -o "${ifname}" -j MASQUERADE 2>/dev/null; then
    iptables -t nat -A POSTROUTING -o "${ifname}" -j MASQUERADE
  fi
  if ! iptables -C FORWARD -i "${ifname}" -o "${lan}" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null; then
    iptables -A FORWARD -i "${ifname}" -o "${lan}" -m state --state RELATED,ESTABLISHED -j ACCEPT
  fi
  if ! iptables -C FORWARD -i "${lan}" -o "${ifname}" -j ACCEPT 2>/dev/null; then
    iptables -A FORWARD -i "${lan}" -o "${ifname}" -j ACCEPT
  fi
  # IPv6 FORWARD/NAT
  if ! ip6tables -t nat -C POSTROUTING -o "${ifname}" -j MASQUERADE 2>/dev/null; then
    ip6tables -t nat -A POSTROUTING -o "${ifname}" -j MASQUERADE
  fi
  if ! ip6tables -C FORWARD -i "${ifname}" -o "${lan}" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null; then
    ip6tables -A FORWARD -i "${ifname}" -o "${lan}" -m state --state RELATED,ESTABLISHED -j ACCEPT
  fi
  if ! ip6tables -C FORWARD -i "${lan}" -o "${ifname}" -j ACCEPT 2>/dev/null; then
    ip6tables -A FORWARD -i "${lan}" -o "${ifname}" -j ACCEPT
  fi
fi

if [ x"${phase}" = xdown ]; then
  iptables -t nat -D POSTROUTING -o "${ifname}" -j MASQUERADE
  iptables -D FORWARD -i "${ifname}" -o "${lan}" -m state --state RELATED,ESTABLISHED -j ACCEPT
  iptables -D FORWARD -i "${lan}" -o "${ifname}" -j ACCEPT
  ip6tables -t nat -D POSTROUTING -o "${ifname}" -j MASQUERADE
  ip6tables -D FORWARD -i "${ifname}" -o "${lan}" -m state --state RELATED,ESTABLISHED -j ACCEPT
  ip6tables -D FORWARD -i "${lan}" -o "${ifname}" -j ACCEPT
fi



exit 0
