#!/usr/bin/env python3
"""
Mode Settings API endpoint
Handles GET (load) and POST (save) operations for mode settings
"""

import os
import logging
from fastapi import APIRouter, Form, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup templates - use relative path from www directory
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Settings directory
ENV_DIR = "/var/lib/rpiap/env"
MODE_FILE = os.path.join(ENV_DIR, "mode")
LAN_FILE = os.path.join(ENV_DIR, "lan")

# Allowed interfaces
ALLOWED_INTERFACES = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "usb0"]


def load_mode():
    """
    Determine mode based on enabled interfaces in ENV_DIR/lan file
    - wlan0 -> AP
    - eth0 + wlan0 -> bridge
    - eth0 -> client
    - ostatní -> custom
    """
    try:
        # Load enabled interfaces
        enabled_interfaces = load_enabled_interfaces()
        
        # Sort interfaces for consistent comparison (like debian/config does)
        sorted_interfaces = sorted(enabled_interfaces)
        
        # Determine mode based on interfaces
        if sorted_interfaces == ["wlan0"]:
            return "ap"
        elif sorted_interfaces == ["eth0"]:
            return "client"
        elif sorted_interfaces == ["eth0", "wlan0"]:
            return "bridge"
        else:
            return "custom"
    except Exception as e:
        logger.error(f"Error loading mode: {e}")
        return "ap"  # Default mode


def load_enabled_interfaces():
    """
    Load enabled interfaces from ENV_DIR/lan file
    Returns list of interface names
    """
    try:
        if os.path.exists(LAN_FILE):
            with open(LAN_FILE, 'r') as f:
                interfaces = [line.strip() for line in f.readlines() if line.strip()]
                # Filter to only allowed interfaces
                return [iface for iface in interfaces if iface in ALLOWED_INTERFACES]
        return ["wlan0"]  # Default
    except Exception as e:
        logger.error(f"Error loading enabled interfaces: {e}")
        return ["wlan0"]


def save_mode(mode: str):
    """
    Save mode to ENV_DIR/mode file
    """
    try:
        if not os.path.exists(ENV_DIR):
            os.makedirs(ENV_DIR, mode=0o700)

        with open(MODE_FILE, 'w') as f:
            f.write(mode)
        os.chmod(MODE_FILE, 0o600)
    except Exception as e:
        logger.error(f"Error saving mode: {e}")
        raise


def save_enabled_interfaces(interfaces: List[str]):
    """
    Save enabled interfaces to ENV_DIR/lan file
    """
    try:
        if not os.path.exists(ENV_DIR):
            os.makedirs(ENV_DIR, mode=0o700)

        # Filter to only allowed interfaces
        valid_interfaces = [iface for iface in interfaces if iface in ALLOWED_INTERFACES]
        
        with open(LAN_FILE, 'w') as f:
            for iface in valid_interfaces:
                f.write(f"{iface}\n")
        os.chmod(LAN_FILE, 0o600)
    except Exception as e:
        logger.error(f"Error saving enabled interfaces: {e}")
        raise


def create_reboot_flag():
    """Create /run/rpiap/need-reboot file when settings are saved"""
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


@router.get("/api/settings/mode", response_class=HTMLResponse)
async def get_mode_settings(request: Request, mode: Optional[str] = Query(None)):
    """Get mode settings form as HTML"""
    try:
        # If mode is provided as query parameter (from select change), use it
        # Otherwise load from file
        if mode and mode in ["ap", "client", "bridge", "custom"]:
            current_mode = mode
        else:
            current_mode = load_mode()
        
        enabled_interfaces = load_enabled_interfaces()
        
        form_html = templates.get_template("partials/settings_mode_form.html").render({
            "request": request,
            "mode": current_mode,
            "enabled_interfaces": enabled_interfaces,
            "allowed_interfaces": ALLOWED_INTERFACES
        })
        return HTMLResponse(content=form_html, status_code=200)
    except Exception as e:
        logger.error(f"Error in get_mode_settings: {e}")
        error_html = templates.get_template("partials/settings_mode_form.html").render({
            "request": request,
            "mode": "ap",
            "enabled_interfaces": ["wlan0"],
            "allowed_interfaces": ALLOWED_INTERFACES,
            "error": f"Error loading mode settings: {str(e)}"
        })
        error_html = HTMLResponse(content=error_html, status_code=500)
        error_html.headers["HX-Trigger"] = "showErrorBar"
        return error_html


@router.post("/api/settings/mode", response_class=HTMLResponse)
async def save_mode_settings(
    request: Request,
    mode: str = Form(...),
    custom_interfaces: Optional[List[str]] = Form(None)
):
    """Save mode settings - POST endpoint, returns HTML form"""
    try:
        # Validate mode
        if mode not in ["ap", "client", "bridge", "custom"]:
            raise ValueError(f"Invalid mode: {mode}")

        # Save mode
        save_mode(mode)

        # Handle interfaces based on mode
        if mode == "custom":
            # Save custom interfaces
            if custom_interfaces:
                save_enabled_interfaces(custom_interfaces)
            else:
                # If no interfaces selected, default to wlan0
                save_enabled_interfaces(["wlan0"])
        elif mode == "ap":
            save_enabled_interfaces(["wlan0"])
        elif mode == "client":
            save_enabled_interfaces(["eth0"])
        elif mode == "bridge":
            save_enabled_interfaces(["eth0", "wlan0"])

        # Create reboot flag
        create_reboot_flag()

        # Reload settings to get current state
        current_mode = load_mode()
        current_enabled_interfaces = load_enabled_interfaces()

        form_html = templates.get_template("partials/settings_mode_form.html").render({
            "request": request,
            "mode": current_mode,
            "enabled_interfaces": current_enabled_interfaces,
            "allowed_interfaces": ALLOWED_INTERFACES
        })

        # Return success response with HX-Trigger to show success status bar and refresh info bar
        response = HTMLResponse(content=form_html, status_code=200)
        response.headers["HX-Trigger"] = '{"showSuccessBar": true, "refreshInfoBar": true}'
        return response

    except Exception as e:
        logger.error(f"Error saving mode settings: {e}")
        error_html_content = templates.get_template("partials/settings_mode_form.html").render({
            "request": request,
            "mode": load_mode(),
            "enabled_interfaces": load_enabled_interfaces(),
            "allowed_interfaces": ALLOWED_INTERFACES,
            "error": f"Error saving mode settings: {str(e)}"
        })
        # Return error response with HX-Trigger to show error status bar
        error_html = HTMLResponse(content=error_html_content, status_code=500)
        error_html.headers["HX-Trigger"] = "showErrorBar"
        return error_html

