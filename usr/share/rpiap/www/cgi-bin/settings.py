#!/usr/bin/env python3

import os
import sys
import cgi
import json
import logging
import traceback
from urllib.parse import parse_qs

# settings directory
ENV_DIR = "/var/lib/rpiap/env"
SETTINGS_JSON = "/usr/share/rpiap/www/settings.json"

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

def send_html_status(status_code=200, message="OK", status_type="success"):
    """
    Send HTML status message fragment.
    """
    print('Content-Type: text/html\n')
    status_html = f'''<div class="status-bar {status_type} visible" id="statusBar" hx-swap-oob="true">
        <span id="statusMessage">{message}</span>
        <button class="status-close" onclick="document.getElementById('statusBar').classList.remove('visible')">×</button>
    </div>'''
    print(status_html)
    sys.exit(0 if status_code // 100 == 2 else 1)

def load_countries():
    """Load countries from settings.json"""
    try:
        with open(SETTINGS_JSON, 'r') as f:
            data = json.load(f)
            return data.get('countries', [])
    except Exception:
        return []

def generate_country_options(selected_country=""):
    """Generate HTML options for country select"""
    countries = load_countries()
    options = []
    for country in countries:
        code = country.get('code', '')
        name = country.get('name', '')
        selected = 'selected' if code == selected_country else ''
        options.append(f'<option value="{code}" {selected}>{code} ({name})</option>')
    return '\n'.join(options)

def generate_channel_options(country_code, selected_channel=""):
    """Generate HTML options for channel select based on country"""
    countries = load_countries()
    country = next((c for c in countries if c.get('code') == country_code), None)
    
    if not country:
        return '<option value="">No channels available</option>'
    
    # Collect all unique channels
    seen = {}
    for ch in country.get('allowed_channels', []):
        ch_id = str(ch.get('id', ''))
        if ch_id not in seen:
            seen[ch_id] = ch.get('description', ch_id)
    
    # Generate options
    options = []
    for ch_id in sorted(seen.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        desc = seen[ch_id]
        selected = 'selected' if ch_id == selected_channel else ''
        options.append(f'<option value="{ch_id}" {selected}>{desc}</option>')
    
    return '\n'.join(options)

def generate_form_html(settings=None):
    """Generate HTML for WLAN settings form"""
    if settings is None:
        settings = {}
    
    wlanssid = settings.get('wlanssid', '')
    wlanpassword = settings.get('wlanpassword', '')
    wlanchannel = str(settings.get('wlanchannel', ''))
    wlancountry = settings.get('wlancountry', '')
    
    country_options = generate_country_options(wlancountry)
    channel_options = generate_channel_options(wlancountry, wlanchannel)
    
    return f'''<form id="wlan-form" class="form-container"
          hx-post="/cgi-bin/settings.py?format=html"
          hx-target="#statusBar"
          hx-swap="outerHTML"
          hx-indicator=".btn-success">
        <div class="form-group">
            <label for="wlanssid">Network Name (SSID):</label>
            <input type="text" id="wlanssid" name="wlanssid" placeholder="Enter network name" value="{wlanssid}" required>
        </div>
        
        <div class="form-group">
            <label for="wlanpassword">Password:</label>
            <div class="password-input-container">
                <input type="password" id="wlanpassword" name="wlanpassword" minlength="8" placeholder="Enter password (min 8 characters)" value="{wlanpassword}">
                <button type="button" class="password-toggle" onclick="togglePasswordVisibility('wlanpassword')">
                    <span class="password-icon">👁️</span>
                </button>
            </div>
        </div>
        
        <div class="form-group">
            <label for="wlanchannel">Channel:</label>
            <select id="wlanchannel" name="wlanchannel">
                {channel_options}
            </select>
        </div>
        
        <div class="form-group">
            <label for="wlancountry">Country:</label>
            <select id="wlancountry" name="wlancountry"
                    hx-get="/cgi-bin/settings.py?action=channels&format=html"
                    hx-target="#wlanchannel"
                    hx-swap="innerHTML"
                    hx-trigger="change">
                {country_options}
            </select>
        </div>
        
        <div class="button-group">
            <button type="submit" class="btn btn-success">Save Settings</button>
            <button type="button" class="btn btn-secondary"
                    hx-get="/cgi-bin/settings.py?format=html"
                    hx-target="#wlan-form"
                    hx-swap="outerHTML">Load Current</button>
        </div>
    </form>'''

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
        with open(key, 'r') as f:
            old_value = f.read().strip()
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

    # Check format parameter
    query_string = os.environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    format_type = query_params.get('format', ['json'])[0]
    action = query_params.get('action', [''])[0]
    request_method = os.environ.get('REQUEST_METHOD', 'GET')

    try:
        os.chdir(ENV_DIR)
        os.chroot(".")
        if os.listdir(".") != os.listdir("/"):
            raise Exception("Internal error: not in chroot")

        form = cgi.FieldStorage()
        flagpostdata = any(form.keys())

        # Handle channel options request
        if action == 'channels' and format_type == 'html':
            # Get country from form or query params
            country_code = ""
            if form.getvalue("wlancountry"):
                country_code = form.getvalue("wlancountry")
            elif 'wlancountry' in query_params:
                country_code = query_params.get('wlancountry', [''])[0]
            print('Content-Type: text/html\n')
            print(generate_channel_options(country_code))
            sys.exit(0)

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
            
            if format_type == 'html':
                send_html_status(200, message, "success")
            else:
                send_json(200, message, settings)
        else:
            settings = load_settings()
            message = "OK"
            
            if format_type == 'html':
                print('Content-Type: text/html\n')
                print(generate_form_html(settings))
                sys.exit(0)
            else:
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

        if format_type == 'html':
            status_type = "error" if status_code >= 400 else "success"
            send_html_status(status_code, status_message, status_type)
        else:
            send_json(status_code, status_message)
