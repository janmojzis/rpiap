# Intro
It is a Debian configuration package that transforms a Raspberry Pi into a wireless access point.

## How it works
Raspberry PI models 3B+, 4, and 5 integrated Wi-Fi interfaces supporting both 2.4 GHz and 5 GHz bands.
The hostapd daemon is used to configure the device as a wireless access point (WLAN), allowing client devices (e.g., PCs, smartphones, ...) to connect.
Internet connectivity (WAN) can be provided either through the onboard Ethernet interface or via USB tethering.

At the network level, `rpiap` creates a local LAN, where Wi-Fi clients can connect.
Traffic from these clients is forwarded to the Internet using network address translation (NAT).

## Components
- The Wi-Fi AP is powered by `hostapd`
- It includes a DHCP server `udhcpd` and client `udhcpc`
- Network Address Translation (NAT) is managed through nftables/iptables."
- DNS service is handled by [dqcache](https://github.com/janmojzis/dq) with support for the [DNSCurve](https://dnscurve.org) protocol
- [PQConnect](https://www.pqconnect.net) is used to encrypt network traffic.

# Installation

## Install Trixie Raspberry Pi OS Lite + install SSH and add ssh-ed25519 public-key
- https://www.raspberrypi.com/software/operating-systems/
- and install Your favorite SSH server (I prefer TinySSH) and insert Your ssh-ed25519 public-key to /root/.ssh/authorized_keys 
~~~
apt-get install tinysshd
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... your@email' >>  /root/.ssh/authorized_keys
~~~

## Install rpiap package
~~~
echo 'deb [trusted=yes] https://raw.githubusercontent.com/janmojzis/rpiap/refs/heads trixie/' > /etc/apt/sources.list.d/rpiap.list
apt-get update
apt-get install rpiap
~~~

## Reconfigure rpiap package

After installation, a local WLAN is created with the network range `192.168.137.0/24`.
The Raspberry Pi uses the address `192.168.137.1`.

Reconfiguration can then be performed via an SSH connection:
~~~
ssh root@192.168.137.1
~~~
~~~
dpkg-reconfigure rpiap
~~~
