#!/usr/bin/env python3
"""
DNS Settings API endpoint
Handles GET (load) and POST (save) operations for DNS settings
"""

import os
import logging
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from fastapi import Query

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


@router.get("/api/settings/dns", response_class=HTMLResponse)
async def get_dns_settings(request: Request, dns_standalone: Optional[str] = Query(None)):
    """Get DNS settings form as HTML"""
    try:
        settings = load_settings()
        
        # If dns_standalone is provided as query parameter, use it (for preview without saving)
        if dns_standalone is not None:
            dns_standalone = dns_standalone.strip().lower()
            if dns_standalone in ("true", "1", "yes", "on"):
                settings["dns_standalone"] = "true"
            else:
                settings["dns_standalone"] = "false"
        
        form_html = templates.get_template("partials/settings_dns_form.html").render({
            "request": request,
            "settings": settings
        })
        return HTMLResponse(content=form_html, status_code=200)
    except Exception as e:
        logger.error(f"Error in get_dns_settings: {e}")
        error_html = templates.get_template("partials/settings_dns_form.html").render({
            "request": request,
            "settings": {},
            "error": f"Error loading DNS settings: {str(e)}"
        })
        error_html = HTMLResponse(content=error_html, status_code=500)
        error_html.headers["HX-Trigger"] = "showErrorBar"
        return error_html


@router.post("/api/settings/dns", response_class=HTMLResponse)
async def save_dns_settings(
    request: Request,
    dns_standalone: Optional[str] = Form("false")
):
    """Save DNS settings - POST endpoint, returns HTML form"""
    try:
        settings = {}

        # Validate dns_standalone - convert to boolean string
        dns_standalone = dns_standalone.strip().lower()
        if dns_standalone in ("true", "1", "yes", "on"):
            settings["dns_standalone"] = "true"
        else:
            settings["dns_standalone"] = "false"

        message = save_settings(settings)
        current_settings = load_settings()

        form_html = templates.get_template("partials/settings_dns_form.html").render({
            "request": request,
            "settings": current_settings
        })

        # Return success response with HX-Trigger to show success status bar and refresh info bar
        response = HTMLResponse(content=form_html, status_code=200)
        response.headers["HX-Trigger"] = '{"showSuccessBar": true, "refreshInfoBar": true}'
        return response

    except Exception as e:
        logger.error(f"Error saving DNS settings: {e}")
        error_html_content = templates.get_template("partials/settings_dns_form.html").render({
            "request": request,
            "settings": load_settings(),
            "error": f"Error saving DNS settings: {str(e)}"
        })
        # Return error response with HX-Trigger to show error status bar
        error_html = HTMLResponse(content=error_html_content, status_code=500)
        error_html.headers["HX-Trigger"] = "showErrorBar"
        return error_html

