#!/usr/bin/env python3
"""
Settings API endpoint
Handles GET (load) and POST (save) operations for WLAN settings
"""

import os
import logging
from fastapi import APIRouter, Form
from typing import Optional

router = APIRouter()

# Settings directory
ENV_DIR = "/var/lib/rpiap/env"

logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s", level=logging.DEBUG)


def load_settings():
    """
    Load settings from individual files in ENV_DIR
    """
    settings = {}
    logmsg = ""
    
    try:
        if not os.path.exists(ENV_DIR):
            logging.warning(f"Settings directory {ENV_DIR} does not exist")
            return settings
            
        for key in os.listdir(ENV_DIR):
            file_path = os.path.join(ENV_DIR, key)
            try:
                if os.path.isfile(file_path):
                    with open(file_path, 'r') as f:
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
    except Exception as e:
        logging.error(f"Error loading settings: {e}")
        
    return settings


def save_settings(settings: dict):
    """
    Save provided settings to files
    """
    logmsg = ""
    
    try:
        if not os.path.exists(ENV_DIR):
            os.makedirs(ENV_DIR, mode=0o700)
            
        for key, value in settings.items():
            file_path = os.path.join(ENV_DIR, key)
            
            try:
                old_value = ""
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        old_value = f.read().strip()
            except FileNotFoundError:
                old_value = ""
            
            if old_value != value:
                with open(file_path, 'w') as f:
                    f.write(value)
                # Set proper permissions
                os.chmod(file_path, 0o600)
                
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
    except Exception as e:
        logging.error(f"Error saving settings: {e}")
        raise


@router.get("/settings")
async def get_settings():
    """Get current settings - GET endpoint"""
    try:
        settings = load_settings()
        return {
            "success": True,
            "message": "OK",
            "settings": settings
        }
    except Exception as e:
        logging.error(f"Error in get_settings: {e}")
        return {
            "success": False,
            "error": f"Error loading settings: {str(e)}"
        }


@router.post("/settings")
async def save_settings_endpoint(
    hostapd_ssid: str = Form(...),
    hostapd_password: Optional[str] = Form(None),
    hostapd_channel: Optional[str] = Form("0"),
    hostapd_country: Optional[str] = Form("")
):
    """Save settings - POST endpoint"""
    try:
        settings = {}
        
        # Validate hostapd_ssid
        hostapd_ssid = hostapd_ssid.strip()
        if not hostapd_ssid:
            return {
                "success": False,
                "error": "SSID is required"
            }
        settings["hostapd_ssid"] = hostapd_ssid

        # Validate hostapd_password
        if hostapd_password:
            hostapd_password = hostapd_password.strip()
            if len(hostapd_password) < 8:
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters"
                }
            settings["hostapd_password"] = hostapd_password

        # Validate hostapd_channel - if not set, use 0 (auto-detect)
        if hostapd_channel:
            hostapd_channel = hostapd_channel.strip()
        if not hostapd_channel:
            hostapd_channel = "0"
        else:
            try:
                ch = int(hostapd_channel)
                if ch < 0 or ch > 165:
                    raise ValueError("Channel out of range")
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid channel number '{hostapd_channel}'"
                }
        settings["hostapd_channel"] = hostapd_channel

        # Validate hostapd_country - if not set, save empty string
        if hostapd_country:
            hostapd_country = hostapd_country.strip()
            # If country is set, validate it
            if len(hostapd_country) != 2 or not hostapd_country.isalpha():
                return {
                    "success": False,
                    "error": f"Invalid country code '{hostapd_country}'"
                }
            settings["hostapd_country"] = hostapd_country
        else:
            # If not set, save empty string
            settings["hostapd_country"] = ""

        message = save_settings(settings)
        current_settings = load_settings()
        
        return {
            "success": True,
            "message": message,
            "settings": current_settings
        }
        
    except Exception as e:
        logging.error(f"Error saving settings: {e}")
        return {
            "success": False,
            "error": f"Error saving settings: {str(e)}"
        }

