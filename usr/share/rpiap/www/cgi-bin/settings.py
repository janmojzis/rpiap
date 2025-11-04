#!/usr/bin/env python3

import os
import sys
import cgi
import json
import logging
import traceback

# settings directory
ENV_DIR = "/var/lib/rpiap/env"

class HTTPException(Exception):
    """
    Custom HTTP exception with a status code and message.
    """
    def __init__(self, status_code: int, status_message: str):
        self.status_code = status_code
        self.status_message = status_message
        super().__init__(f"[{status_code}] {status_message}")

def send_json(status_code=200, message="OK", data=None):
    """
    Unified JSON response with current settings.
    """
    print(f'Status: {status_code}')
    print('Content-type: application/json')
    print()

    if status_code // 100 == 2:
        resp = {"success": True, "message": message}
    else:
        resp = {"success": False, "error": message}

    if data is not None:
        resp["settings"] = data

    print(json.dumps(resp))
    sys.exit(0 if status_code // 100 == 2 else 1)

def load_settings():
    """
    Load settings from individual files in ENV_DIR
    """
    settings = {}
    logmsg = ""
    for key in os.listdir('.'):
        try:
            with open(key, 'r') as f:
                value = f.read().strip()
        except Exception:
            continue

        if "password" in key:
            settings[key] = ""
            logmsg += f"{key}: [HIDDEN], "
        else:
            settings[key] = value
            logmsg += f"{key}: {value}, "

    if logmsg.endswith(", "):
        logmsg = logmsg[:-2]
    logging.debug(logmsg)
    return settings

def save_settings(settings):
    """
    Save provided settings to files
    """
    logmsg = ""
    for key, value in settings.items():
        try:
            with open(key, 'r') as f:
                old_value = f.read().strip()
        except FileNotFoundError:
            old_value = ""
        
        if old_value != value:
            with open(key, 'w') as f:
                f.write(value)
            if "password" in key:
                logmsg += f"{key}: updated, "
            else:
                logmsg += f"{key}: {old_value} -> {value}, "

    if logmsg.endswith(", "):
        logmsg = logmsg[:-2]

    if logmsg:
        logging.debug(logmsg)
        return "Settings saved successfully"
    return "Nothing changed"

if __name__ == "__main__":
    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.DEBUG)

    try:
        os.chdir(ENV_DIR)
        os.chroot(".")
        if os.listdir(".") != os.listdir("/"):
            raise Exception("Internal error: not in chroot")

        form = cgi.FieldStorage()
        flagpostdata = any(form.keys())

        if flagpostdata:
            settings = {}

            # validate hostapd_ssid
            hostapd_ssid = form.getvalue("hostapd_ssid", "").strip()
            if not hostapd_ssid:
                raise HTTPException(400, "SSID is required")
            settings["hostapd_ssid"] = hostapd_ssid

            # validate hostapd_password
            hostapd_password = form.getvalue("hostapd_password", "").strip()
            if hostapd_password:
                if len(hostapd_password) < 8:
                    raise HTTPException(400, "Password must be at least 8 characters")
                settings["hostapd_password"] = hostapd_password

            # validate hostapd_channel - if not set, use 0 (auto-detect)
            hostapd_channel = form.getvalue("hostapd_channel", "").strip()
            if not hostapd_channel:
                hostapd_channel = "0"
            else:
                try:
                    ch = int(hostapd_channel)
                    if ch < 0 or ch > 165:
                        raise ValueError("Channel out of range")
                    # If 0 is set, it's valid (auto-detect)
                except ValueError:
                    raise HTTPException(400, f"Invalid channel number '{hostapd_channel}'")
            settings["hostapd_channel"] = hostapd_channel

            # validate hostapd_country - if not set, don't save it
            hostapd_country = form.getvalue("hostapd_country", "").strip()
            if hostapd_country:
                if len(hostapd_country) != 2 or not hostapd_country.isalpha():
                    raise HTTPException(400, f"Invalid country code '{hostapd_country}'")
                settings["hostapd_country"] = hostapd_country
            # If not set, don't save it (won't be in settings)

            message = save_settings(settings)
        else:
            settings = load_settings()
            message = "OK"

        send_json(200, message, settings)


    except Exception as e:
        if isinstance(e, HTTPException):
            status_code = e.status_code
            status_message = e.status_message
        else:
            status_code = 500
            status_message = str(e)
            # capture full traceback and log it
            tb_str = traceback.format_exc()
            logging.fatal(f"Unexpected error: {str(e)}")
            logging.fatal(f"Traceback: {tb_str}")

        send_json(status_code, status_message)
