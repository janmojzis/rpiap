# Intro
It is a Debian configuration package that transforms a Raspberry Pi into a wireless access point.

## How it works
Raspberry PI models 3B+, 4, and 5 integrated Wi-Fi interfaces supporting both 2.4 GHz and 5 GHz bands.
The hostapd daemon is used to configure the device as a wireless access point (WLAN), allowing client devices (e.g., PCs, smartphones, ...) to connect.
Internet connectivity (WAN) can be provided either through the onboard Ethernet interface or via USB tethering.

## Components
- The Wi-Fi AP is powered by `hostapd`
- It includes a DHCP server `udhcpd` and client `udhcpc`
- DNS services are handled by [dqcache](https://github.com/janmojzis/dq) with support for the [DNSCurve](https://dnscurve.org) protocol
- [PQConnect](https://www.pqconnect.net) is used to encrypt network traffic.

# Installation

## Install Raspberry Pi OS Lite
- https://www.raspberrypi.com/software/operating-systems/

## Upgrade Raspberry Pi OS to trixie
~~~
sed -i 's/bookworm/trixie/g' /etc/apt/sources.list /etc/apt/sources.list.d/*
apt-get update
apt full-upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confnew" --purge --auto-remove
~~~

## Install rpiap package
~~~
echo 'deb [trusted=yes] https://raw.githubusercontent.com/janmojzis/rpiap/refs/heads trixie/' > /etc/apt/sources.list.d/rpiap.list
apt-get update
apt-get install rpiap
~~~
