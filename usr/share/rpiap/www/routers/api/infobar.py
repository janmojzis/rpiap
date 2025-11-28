#!/usr/bin/env python3
"""
Infobar router - handles /api/infobar endpoint
"""

import os
import hashlib
import logging
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, HTMLResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Info bar file path
INFOBAR_FILE = "/run/rpiap/infobar"

# Environment directories for comparison
ENV_PERSIST_DIR = "/var/lib/rpiap/env"
ENV_RUN_DIR = "/run/rpiap/env"


def env_dirs_differ():
    """
    Check if persist env dir (/var/lib/rpiap/env) and run env dir (/run/rpiap/env) differ in content.

    Returns False if either directory doesn't exist or if they have identical content.
    Returns True if they differ in any way (missing/extra files, different content).
    """
    changed_files = get_changed_files()
    return len(changed_files) > 0


def get_changed_files():
    """
    Get list of files that differ between persist env dir (/var/lib/rpiap/env) 
    and run env dir (/run/rpiap/env).

    Returns list of relative paths of changed files (missing, extra, or different content).
    Returns empty list if directories don't exist or are identical.
    """
    changed_files = []
    
    if not os.path.exists(ENV_PERSIST_DIR) or not os.path.exists(ENV_RUN_DIR):
        return changed_files

    try:
        # Get list of files in both directories (only regular files)
        persist_files = set()
        run_files = set()

        for dirname, dirs, files in os.walk(ENV_PERSIST_DIR):
            for filename in files:
                rel_path = os.path.relpath(os.path.join(dirname, filename), ENV_PERSIST_DIR)
                persist_files.add(rel_path)

        for dirname, dirs, files in os.walk(ENV_RUN_DIR):
            for filename in files:
                rel_path = os.path.relpath(os.path.join(dirname, filename), ENV_RUN_DIR)
                run_files.add(rel_path)

        # Check for files missing in run dir (present in persist but not in run)
        for rel_path in persist_files - run_files:
            logger.debug("Env dirs differ: file %s missing in run dir", rel_path)
            changed_files.append(rel_path)

        # Check for extra files in run dir (present in run but not in persist)
        for rel_path in run_files - persist_files:
            logger.debug("Env dirs differ: file %s extra in run dir", rel_path)
            changed_files.append(rel_path)

        # Check content of each file that exists in both
        for rel_path in persist_files & run_files:
            persist_file = os.path.join(ENV_PERSIST_DIR, rel_path)
            run_file = os.path.join(ENV_RUN_DIR, rel_path)

            # Compare file contents using SHA256
            persist_hash = hashlib.sha256()
            run_hash = hashlib.sha256()

            with open(persist_file, 'rb') as f:
                persist_hash.update(f.read())

            with open(run_file, 'rb') as f:
                run_hash.update(f.read())

            if persist_hash.hexdigest() != run_hash.hexdigest():
                logger.debug("Env dirs differ: file %s has different content", rel_path)
                changed_files.append(rel_path)

        if not changed_files:
            logger.debug("Env dirs are identical")

    except Exception as e:
        logger.error("Error comparing env directories: %s", e)
        return []

    return sorted(changed_files)


@router.get("/api/infobar", response_class=PlainTextResponse)
async def infobar_get(request: Request):
    """Get infobar content - returns plain text content based on manual activation or env dir differences"""
    try:
        # First check for manually activated infobar file (for backward compatibility)
        if os.path.exists(INFOBAR_FILE):
            # Read file content and return it directly as plain text
            with open(INFOBAR_FILE, 'r') as f:
                content = f.read().strip()
                if content:  # Only return if file has content
                    return PlainTextResponse(content=content, status_code=200)

        # If no manual infobar, check if env directories differ
        changed_files = get_changed_files()
        if changed_files:
            # Build message with list of changed files
            message = "Settings have been changed. Please restart the service to apply the new configuration."
            message += "\n\nChanged files: " + ", ".join(changed_files)
            return PlainTextResponse(content=message, status_code=200)

        # No infobar needed - return empty (infobar will be hidden)
        return PlainTextResponse(content="", status_code=200)
    except Exception as e:
        logger.error("Error getting infobar content: %s", e)
        # On error, return empty
        return PlainTextResponse(content="", status_code=200)


@router.post("/api/infobar/activate", response_class=HTMLResponse)
async def infobar_activate(request: Request):
    """Create infobar file with default message and trigger refresh"""
    try:
        # Create directory if it doesn't exist
        infobar_dir = "/run/rpiap"
        if not os.path.exists(infobar_dir):
            os.makedirs(infobar_dir, mode=0o755)

        # Create/write the infobar file with default message
        with open(INFOBAR_FILE, 'w') as f:
            f.write("Settings changed")
        os.chmod(INFOBAR_FILE, 0o644)

        # Trigger infobar refresh
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "refreshInfoBar"
        return response
    except Exception as e:
        logger.error(f"Error activating infobar: {e}")
        return HTMLResponse(content="Error activating infobar", status_code=500)


@router.post("/api/infobar/deactivate", response_class=HTMLResponse)
async def infobar_deactivate(request: Request):
    """Remove infobar file and trigger refresh"""
    try:
        # Remove the infobar file if it exists
        if os.path.exists(INFOBAR_FILE):
            os.remove(INFOBAR_FILE)

        # Trigger infobar refresh
        response = HTMLResponse(content="", status_code=200)
        response.headers["HX-Trigger"] = "refreshInfoBar"
        return response
    except Exception as e:
        logger.error(f"Error deactivating infobar: {e}")
        return HTMLResponse(content="Error deactivating infobar", status_code=500)
