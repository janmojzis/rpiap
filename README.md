# Intro
Raspberry PI models 3B+, 4, and 5 integrated Wi-Fi interfaces supporting both 2.4 GHz and 5 GHz bands.

The `rpiap` package provides flexible network configuration capabilities, allowing you to use different combinations of WiFi, Ethernet, and USB network interfaces for LAN and WAN connectivity. Depending on the selected operating mode, the Raspberry Pi can create its own wireless network, connect as a client to an existing Wifi network, integrate into your existing LAN infrastructure, or be configured in custom topologies. The package handles network interface management, DHCP services, DNS resolution, and network address translation (NAT) automatically.

# Operating Modes

The package supports two standard operating modes and two advanced modes that can be selected during installation or reconfiguration using `dpkg-reconfigure rpiap`:

### ap (Access Point mode, default)
The WiFi interface operates as an access point, creating a wireless LAN network for client devices to connect to. The Ethernet interface or USB devices (such as a mobile phone via tethering) can be used as the WAN connection to the Internet. This is the standard configuration for a home router.

### client (Wireless Client mode)
The Ethernet interface is used to provide LAN connectivity for connected wired devices. The WiFi interface connects to another access point as a client, providing WAN Internet access through the wireless connection. This mode is useful when you want to extend Internet access to wired devices through an existing WiFi network.

### bridge (Bridge mode)
Bridges the Ethernet and wireless interfaces together, integrating the wireless access point directly into your existing LAN infrastructure. All devices, whether connected via Ethernet or WiFi, will be on the same network segment, sharing the same IP address range and network resources. For advanced users only.

### custom (Custom mode)
Allows you to select your own combination of LAN interfaces. For advanced users only.

## Components
- The Wi-Fi AP is powered by `hostapd`
- It includes a DHCP server `udhcpd` and client `udhcpc`
- Network Address Translation (NAT) is managed through nftables/iptables."
- DNS service is handled by [dqcache](https://github.com/janmojzis/dq) with support for the [DNSCurve](https://dnscurve.org) protocol
- [PQConnect](https://www.pqconnect.net) is used to encrypt network traffic.

# Installation

## Install Trixie Raspberry Pi OS Lite, install SSH, add ssh-ed25519 public-key
- https://www.raspberrypi.com/software/operating-systems/
- and install Your favorite SSH server (I prefer TinySSH) and insert Your ssh-ed25519 public-key to /root/.ssh/authorized_keys 
~~~
apt-get install tinysshd
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... your@email' >>  /root/.ssh/authorized_keys
~~~
Note: replace `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... your@email` with Your ssh-ed25519 public-key

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
