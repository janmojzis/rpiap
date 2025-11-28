#!/usr/bin/env python3
"""
WLAN Settings API endpoint
Handles GET (load) and POST (save) operations for WLAN settings
"""

import os
import json
import logging
from fastapi import APIRouter, Form, Request, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup templates - use relative path from www directory
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Settings directory
ENV_DIR = "/var/lib/rpiap/env"


def load_settings():
    """
    Load settings from individual files in ENV_DIR
    """
    settings = {}

    try:
        if not os.path.exists(ENV_DIR):
            logger.warning(f"Settings directory {ENV_DIR} does not exist")
            return settings

        for key in os.listdir(ENV_DIR):
            file_path = os.path.join(ENV_DIR, key)
            try:
                if os.path.isfile(file_path):
                    with open(file_path, 'r') as f:
                        value = f.read().strip()
                    if "password" in key:
                        settings[key] = ""
                    else:
                        settings[key] = value
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Error loading settings: {e}")

    return settings


def save_settings(settings: dict):
    """
    Save provided settings to files
    """
    try:
        if not os.path.exists(ENV_DIR):
            os.makedirs(ENV_DIR, mode=0o700)

        for key, value in settings.items():
            file_path = os.path.join(ENV_DIR, key)

            try:
                with open(file_path, 'w') as f:
                    f.write(value)
                # Set proper permissions
                os.chmod(file_path, 0o600)
            except Exception as e:
                logger.error(f"Error saving {key}: {e}")

        # Create /run/rpiap/need-reboot file when any settings are saved
        try:
            reboot_flag_dir = "/run/rpiap"
            reboot_flag_file = os.path.join(reboot_flag_dir, "need-reboot")
            if not os.path.exists(reboot_flag_dir):
                os.makedirs(reboot_flag_dir, mode=0o755)
            with open(reboot_flag_file, 'w') as f:
                f.write("")
            os.chmod(reboot_flag_file, 0o644)
        except Exception as e:
            logger.warning(f"Could not create need-reboot file: {e}")

        return "Settings saved successfully"
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        raise


def load_countries_data():
    """Load countries data from settings.json"""
    settings_json_path = os.path.join(BASE_DIR, "static", "settings.json")
    try:
        with open(settings_json_path, 'r') as f:
            data = json.load(f)
            return data.get("countries", [])
    except Exception as e:
        logger.error(f"Error loading countries data: {e}")
        return []


def prepare_form_data(settings: dict = None, country: str = None):
    """Prepare countries and channels data for the form"""
    if settings is None:
        settings = load_settings()
    
    countries = load_countries_data()
    current_country = country if country is not None else settings.get("hostapd_country", "")
    current_channel = settings.get("hostapd_channel", "0")
    
    # Collect all unique channels from all countries
    all_channels = {}
    for c in countries:
        for ch in c.get("allowed_channels", []):
            if ch["id"] not in all_channels:
                all_channels[ch["id"]] = ch["description"]
    
    # Find country data to determine which channels are allowed
    country_data = None
    for c in countries:
        country_code = c.get("code", "")
        if str(country_code) == str(current_country):
            country_data = c
            break
    
    # Get allowed channel IDs for selected country
    allowed_channel_ids = set()
    if country_data:
        allowed_channel_ids = {ch["id"] for ch in country_data.get("allowed_channels", [])}
    else:
        # If no country selected or country not found, only channel 0 is allowed
        allowed_channel_ids = {0}
    
    # Build channels list with all channels, disabled if not allowed
    channels = []
    for channel_id in sorted(all_channels.keys()):
        is_disabled = channel_id not in allowed_channel_ids
        description = all_channels[channel_id]
        if is_disabled:
            description = description.replace(" (unavailable)", "") + " (unavailable)"
        channels.append({
            "id": channel_id,
            "description": description,
            "disabled": is_disabled
        })
    
    return {
        "countries": countries,
        "current_country": current_country,
        "channels": channels,
        "current_channel": current_channel
    }


@router.get("/api/settings/countries", response_class=HTMLResponse)
async def get_countries_select(request: Request):
    """Get countries select as HTML"""
    try:
        countries = load_countries_data()
        settings = load_settings()
        current_country = settings.get("hostapd_country", "")
        return templates.TemplateResponse("partials/countries_select.html", {
            "request": request,
            "countries": countries,
            "current_country": current_country
        })
    except Exception as e:
        logger.error(f"Error loading countries: {e}")
        return HTMLResponse(content=f"<select><option>Error loading countries</option></select>", status_code=500)


@router.get("/api/settings/channels", response_class=HTMLResponse)
async def get_channels_select(request: Request, hostapd_country: str = Query(None, alias="hostapd_country")):
    """Get channels select as HTML based on country"""
    try:
        countries = load_countries_data()
        settings = load_settings()
        current_channel = settings.get("hostapd_channel", "0")
        
        # Get country from query parameter or settings, handling empty string correctly
        if hostapd_country is not None:
            country = hostapd_country
        else:
            country = settings.get("hostapd_country", "")
        
        # Collect all unique channels from all countries
        all_channels = {}
        for c in countries:
            for ch in c.get("allowed_channels", []):
                if ch["id"] not in all_channels:
                    all_channels[ch["id"]] = ch["description"]
        
        # Find country data to determine which channels are allowed
        # Handle empty string country code (for "Not set")
        country_data = None
        for c in countries:
            country_code = c.get("code", "")
            # Compare both as strings, handling empty string case
            if str(country_code) == str(country):
                country_data = c
                break
        
        # Get allowed channel IDs for selected country
        allowed_channel_ids = set()
        if country_data:
            allowed_channel_ids = {ch["id"] for ch in country_data.get("allowed_channels", [])}
        else:
            # If no country selected or country not found, only channel 0 is allowed
            allowed_channel_ids = {0}
        
        # Build channels list with all channels, disabled if not allowed
        # Add "(unavailable)" to description if disabled
        channels = []
        for channel_id in sorted(all_channels.keys()):
            is_disabled = channel_id not in allowed_channel_ids
            description = all_channels[channel_id]
            if is_disabled:
                # Remove "(unavailable)" if already present, then add it
                description = description.replace(" (unavailable)", "") + " (unavailable)"
            channels.append({
                "id": channel_id,
                "description": description,
                "disabled": is_disabled
            })
        
        return templates.TemplateResponse("partials/channels_select.html", {
            "request": request,
            "channels": channels,
            "current_channel": current_channel
        })
    except Exception as e:
        logger.error(f"Error loading channels: {e}")
        return HTMLResponse(content=f"<select><option>Error loading channels</option></select>", status_code=500)


@router.get("/api/settings/wlan", response_class=HTMLResponse)
async def get_wlan_settings(request: Request, password_visible: Optional[str] = Query(None)):
    """Get WLAN settings form as HTML"""
    try:
        settings = load_settings()
        form_data = prepare_form_data(settings)
        
        # Determine password visibility state
        # If password_visible is provided, use it; otherwise default to False (password hidden)
        show_password = password_visible == "true" if password_visible is not None else False
        
        form_html = templates.get_template("partials/settings_wlan_form.html").render({
            "request": request,
            "settings": settings,
            "password_visible": show_password,
            "password_value": "",
            **form_data
        })
        return HTMLResponse(content=form_html, status_code=200)
    except Exception as e:
        logger.error(f"Error in get_wlan_settings: {e}")
        error_message = f"Error loading WLAN settings: {str(e)}"
        error_response = PlainTextResponse(content=error_message, status_code=500)
        error_response.headers["HX-Trigger"] = json.dumps({"showErrorBar": {"message": error_message}})
        return error_response


@router.post("/api/settings/wlan/toggle", response_class=HTMLResponse)
async def toggle_password_visibility(
    request: Request,
    password_visible: Optional[str] = Form(None),
    hostapd_password: Optional[str] = Form(None)
):
    """Toggle password visibility - returns form with toggled state"""
    try:
        settings = load_settings()
        form_data = prepare_form_data(settings)
        
        # Determine password visibility state
        show_password = password_visible == "true" if password_visible is not None else False
        
        # Get password value from form if provided
        password_value = hostapd_password if hostapd_password is not None else ""
        
        form_html = templates.get_template("partials/settings_wlan_form.html").render({
            "request": request,
            "settings": settings,
            "password_visible": show_password,
            "password_value": password_value,
            **form_data
        })
        return HTMLResponse(content=form_html, status_code=200)
    except Exception as e:
        logger.error(f"Error in toggle_password_visibility: {e}")
        error_html = templates.get_template("partials/settings_wlan_form.html").render({
            "request": request,
            "settings": {},
            "password_visible": False,
            "password_value": "",
            "countries": [],
            "current_country": "",
            "channels": [],
            "current_channel": "0",
            "error": f"Error toggling password visibility: {str(e)}"
        })
        error_html = HTMLResponse(content=error_html, status_code=500)
        error_html.headers["HX-Trigger"] = "showErrorBar"
        return error_html


@router.post("/api/settings/wlan", response_class=HTMLResponse)
async def save_wlan_settings(
    request: Request,
    hostapd_ssid: str = Form(...),
    hostapd_password: Optional[str] = Form(None),
    hostapd_channel: Optional[str] = Form("0"),
    hostapd_country: Optional[str] = Form("")
):
    """Save WLAN settings - POST endpoint, returns HTML form"""
    try:
        settings = {}
        
        # Validate hostapd_ssid
        hostapd_ssid = hostapd_ssid.strip()
        if not hostapd_ssid:
            error_message = "SSID is required"
            error_response = PlainTextResponse(content=error_message, status_code=400)
            error_response.headers["HX-Trigger"] = json.dumps({"showErrorBar": {"message": error_message}})
            return error_response
        settings["hostapd_ssid"] = hostapd_ssid

        # Validate hostapd_password
        if hostapd_password:
            hostapd_password = hostapd_password.strip()
            if len(hostapd_password) < 8:
                error_message = "Password must be at least 8 characters"
                error_response = PlainTextResponse(content=error_message, status_code=400)
                error_response.headers["HX-Trigger"] = json.dumps({"showErrorBar": {"message": error_message}})
                return error_response
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
                error_message = f"Invalid channel number '{hostapd_channel}'"
                error_response = PlainTextResponse(content=error_message, status_code=400)
                error_response.headers["HX-Trigger"] = json.dumps({"showErrorBar": {"message": error_message}})
                return error_response
        settings["hostapd_channel"] = hostapd_channel

        # Validate hostapd_country - if not set, save empty string
        if hostapd_country:
            hostapd_country = hostapd_country.strip()
            # If country is set, validate it
            if len(hostapd_country) != 2 or not hostapd_country.isalpha():
                error_message = f"Invalid country code '{hostapd_country}'"
                error_response = PlainTextResponse(content=error_message, status_code=400)
                error_response.headers["HX-Trigger"] = json.dumps({"showErrorBar": {"message": error_message}})
                return error_response
            settings["hostapd_country"] = hostapd_country
        else:
            # If not set, save empty string
            settings["hostapd_country"] = ""

        message = save_settings(settings)
        current_settings = load_settings()
        form_data = prepare_form_data(current_settings)

        form_html = templates.get_template("partials/settings_wlan_form.html").render({
            "request": request,
            "settings": current_settings,
            "password_visible": False,
            "password_value": "",
            **form_data
        })

        # Return success response with HX-Trigger to show success status bar and refresh info bar
        response = HTMLResponse(content=form_html, status_code=200)
        response.headers["HX-Trigger"] = '{"showSuccessBar": true, "refreshInfoBar": true}'
        return response

    except Exception as e:
        logger.error(f"Error saving WLAN settings: {e}")
        error_message = f"Error saving WLAN settings: {str(e)}"
        error_response = PlainTextResponse(content=error_message, status_code=500)
        error_response.headers["HX-Trigger"] = json.dumps({"showErrorBar": {"message": error_message}})
        return error_response

