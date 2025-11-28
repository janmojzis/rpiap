from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from routers import home, test_button, test, test_ui, test_select, settings, speedtest
from routers.api import (
    infobar as api_infobar,
    successbar as api_successbar,
    errorbar as api_errorbar,
    sidebar,
    settings_dns,
    settings_wlan,
    settings_wcli,
    settings_mode,
    settings_theme,
    speedtest as api_speedtest,
    interfaces as api_interfaces,
    test_select as api_test_select,
)
import logging
import os
import shutil

# Configure debug logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def init_run_env_dir():
    """Initialize /run/rpiap/env directory by copying from /var/lib/rpiap/env if it doesn't exist."""
    env_persist_dir = "/var/lib/rpiap/env"
    env_run_dir = "/run/rpiap/env"

    # If run env dir already exists, do nothing
    if os.path.exists(env_run_dir):
        logger.debug("Run env directory %s already exists, skipping initialization", env_run_dir)
        return

    # If persist env dir doesn't exist, do nothing
    if not os.path.exists(env_persist_dir):
        logger.warning("Persist env directory %s does not exist, cannot initialize run env", env_persist_dir)
        return

    try:
        # Create run env directory
        os.makedirs(env_run_dir, mode=0o755, exist_ok=True)

        # Copy all files from persist to run env dir
        for filename in os.listdir(env_persist_dir):
            src_file = os.path.join(env_persist_dir, filename)
            dst_file = os.path.join(env_run_dir, filename)

            # Only copy regular files, skip directories and special files
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                logger.debug("Copied %s to %s", src_file, dst_file)

        logger.info("Initialized run env directory %s from %s", env_run_dir, env_persist_dir)
    except Exception as e:
        logger.error("Failed to initialize run env directory: %s", e)


class NoCacheStaticFiles(StaticFiles):
    """Custom StaticFiles with Cache-Control reponse header. """

    async def get_response(self, path: str, scope):
        """Override to add proper caching headers and Not Modified responses."""
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        # HTTP/1.0 compatibility
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

# Create app without session middleware (using query parameters instead)
app = FastAPI(
    title="UI for rpiap",
    description="Web UI for RPIAP system",
    version="1.0.0"
)

# Initialize run env directory on app startup
init_run_env_dir()

# Function for getting current theme from query parameter or default
def get_current_theme(request: Request):
    """Get current theme from query parameter or default."""
    theme = request.query_params.get("theme", "default")

    # Validate theme - only support default and dark modes
    valid_themes = ["default", "dark"]
    if theme not in valid_themes:
        theme = "default"

    return theme

# Mount static files with improved caching
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# Include routers
app.include_router(home.router)
app.include_router(test_button.router)
app.include_router(test.router)
app.include_router(test_ui.router)
app.include_router(test_select.router)
app.include_router(settings.router)
app.include_router(speedtest.router)

# Include api routers
app.include_router(api_infobar.router)
app.include_router(api_successbar.router)
app.include_router(api_errorbar.router)
app.include_router(sidebar.router)
app.include_router(settings_dns.router)
app.include_router(settings_wlan.router)
app.include_router(settings_wcli.router)
app.include_router(settings_mode.router)
app.include_router(settings_theme.router)
app.include_router(api_speedtest.router, prefix="/api")
app.include_router(api_interfaces.router, prefix="/api")
app.include_router(api_test_select.router, prefix="/api")
