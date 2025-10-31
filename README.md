# Intro
Raspberry PI models 3B+, 4, and 5 integrated Wi-Fi interfaces supporting both 2.4 GHz and 5 GHz bands.

The `rpiap` package provides flexible network configuration capabilities, allowing you to use different combinations of WiFi, Ethernet, and USB network interfaces for LAN and WAN connectivity. Depending on the selected operating mode, the Raspberry Pi can create its own wireless network, connect as a client to an existing Wifi network, integrate into your existing LAN infrastructure, or be configured in custom topologies.

The `rpiap` package is a configuration package only, it installs and uses existing Debian packages and does not include any precompiled binaries

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

Follow these steps to install and configure rpiap on your Raspberry Pi.

## Step 1: Prepare Your Raspberry Pi

### Install Raspberry Pi OS Lite (Trixie)

1. Download **Raspberry Pi OS Lite (Trixie)** from the official website:
   - 🔗 [raspberrypi.com/software/operating-systems/](https://www.raspberrypi.com/software/operating-systems/)
2. Flash the image to your SD card using your preferred tool (e.g., Raspberry Pi Imager)

## Step 2: Install rpiap

Boot your Raspberry Pi and connect (via console or SSH). Then add the rpiap repository and install:

```bash
echo 'deb [trusted=yes] https://raw.githubusercontent.com/janmojzis/rpiap/refs/heads trixie/' > /etc/apt/sources.list.d/rpiap.list
apt-get update
apt-get install rpiap
```

> **What happens next:** The installation process will guide you through interactive configuration. The default setup creates a wireless access point network.

**Default network configuration:**
- IP range: `192.168.137.0/24`
- Gateway: `192.168.137.1`
- After installation, connect to the WLAN network to access the device

## Step 3: Reconfigure (Optional)

You can reconfigure rpiap settings at any time. Connect via SSH or locally:

```bash
# If connecting remotely:
ssh root@192.168.137.1

# Then reconfigure:
dpkg-reconfigure rpiap
```

This allows you to change operating modes (ap, client, bridge, custom) and network settings.

