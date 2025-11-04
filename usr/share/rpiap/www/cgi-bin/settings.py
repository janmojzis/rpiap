#!/usr/bin/env python3

import os
import sys
import cgi
import json
import logging
import traceback

# settings directory
ENV_DIR = "/var/lib/rpiap/env"

# Mapping from form field names to environment variable names
FORM_TO_ENV_MAP = {
    "wlanssid": "hostapd_ssid",
    "wlanpassword": "hostapd_password",
    "wlanchannel": "hostapd_channel",
    "wlancountry": "hostapd_country",
}

# Reverse mapping from environment variable names to form field names
ENV_TO_FORM_MAP = {v: k for k, v in FORM_TO_ENV_MAP.items()}

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
    Maps environment variable names back to form field names for frontend compatibility
    """
    settings = {}
    logmsg = ""
    for key in os.listdir('.'):
        try:
            with open(key, 'r') as f:
                value = f.read().strip()
        except Exception:
            continue

        # Map environment variable name to form field name if mapping exists
        form_key = ENV_TO_FORM_MAP.get(key, key)
        
        if "password" in key:
            settings[form_key] = ""
            logmsg += f"{key}: [HIDDEN], "
        else:
            settings[form_key] = value
            logmsg += f"{key}: {value}, "

    if logmsg.endswith(", "):
        logmsg = logmsg[:-2]
    logging.debug(logmsg)
    return settings

def save_settings(settings):
    """
    Save provided settings to files
    Maps form field names to environment variable names before saving
    """
    logmsg = ""
    for form_key, value in settings.items():
        # Map form field name to environment variable name if mapping exists
        env_key = FORM_TO_ENV_MAP.get(form_key, form_key)
        
        try:
            with open(env_key, 'r') as f:
                old_value = f.read().strip()
        except FileNotFoundError:
            old_value = ""
        
        if old_value != value:
            with open(env_key, 'w') as f:
                f.write(value)
            if "password" in env_key:
                logmsg += f"{env_key}: updated, "
            else:
                logmsg += f"{env_key}: {old_value} -> {value}, "

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

            # validate wlanssid
            wlanssid = form.getvalue("wlanssid", "").strip()
            if not wlanssid:
                raise HTTPException(400, "SSID is required")
            settings["wlanssid"] = wlanssid

            # validate wlanpassword
            wlanpassword = form.getvalue("wlanpassword", "").strip()
            if wlanpassword:
                if len(wlanpassword) < 8:
                    raise HTTPException(400, "Password must be at least 8 characters")
                settings["wlanpassword"] = wlanpassword

            # validate wlanchannel
            wlanchannel = form.getvalue("wlanchannel", "").strip()
            try:
                ch = int(wlanchannel)
                if ch < 1 or ch > 165:
                    raise ValueError("Channel out of range")
            except ValueError:
                raise HTTPException(400, f"Invalid channel number '{wlanchannel}'")
            settings["wlanchannel"] = wlanchannel

            # validate wlancountry
            wlancountry = form.getvalue("wlancountry", "").strip()
            if len(wlancountry) != 2 or not wlancountry.isalpha():
                raise HTTPException(400, f"Invalid country code '{wlancountry}'")
            settings["wlancountry"] = wlancountry

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
