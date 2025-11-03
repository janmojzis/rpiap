#!/usr/bin/env python3

import hashlib, binascii, sys, os, re

ssid = os.getenv("wlan_ssid")
if ssid is None:
    raise Exception("$wlan_ssid not set")

password = os.getenv("wlan_password")
if password is None:
    raise Exception("$wlan_password not set")
if len(password) < 8:
    raise Exception("$wlan_password must be at least 8 characters")

channel = os.getenv("wlan_channel")
if channel is None:
    channel = "0"

if int(channel) > 0 and int(channel) < 14:
    mode = "g"
else:
    mode = "a"

country = os.getenv("wlan_country")
if country is None:
    country = "CZ"

psk = hashlib.pbkdf2_hmac("sha1", password.encode('utf-8'), ssid.encode('utf-8'), 4096, 32)
psk = binascii.hexlify(psk).decode()

data = open(sys.argv[1]).read()
data = re.sub("__SSID__", ssid, data)
data = re.sub("__PSK__", psk, data)
data = re.sub("__COUNTRY__", country, data)
data = re.sub("__CHANNEL__", channel, data)
data = re.sub("__MODE__", mode, data)

print(data)
