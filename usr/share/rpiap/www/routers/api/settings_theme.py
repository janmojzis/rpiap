#!/usr/bin/env python3
"""
Settings Theme router - handles /api/theme endpoint for theme switching
"""

import os
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Valid themes
VALID_THEMES = [
    "default", "dark"
]


@router.post("/api/theme")
async def switch_theme(request: Request, theme: str = Form(...)) -> HTMLResponse:
    """Switch theme and return HTML with script to execute theme change.

    Args:
        request: FastAPI request object.
        theme: Theme name from form data.

    Returns:
        HTMLResponse: HTML with script to update theme.
    """
    try:
        # Validate theme
        if theme not in VALID_THEMES:
            logger.warning("Invalid theme requested: %s", theme)
            theme = "default"

        logger.debug("Theme switched to: %s", theme)

        # Return HTML with script to update theme
        # This will update the html element's data-theme attribute via JavaScript
        if theme == "default":
            script = '''
                // Remove data-theme attribute for default theme
                document.documentElement.removeAttribute('data-theme');
            '''
        else:
            script = f'''
                // Update data-theme attribute on html element
                document.documentElement.setAttribute('data-theme', '{theme}');
            '''

        return HTMLResponse(
            f'''<script>
                {script}
                // Update URL to include theme parameter for persistence
                const url = new URL(window.location);
                url.searchParams.set('theme', '{theme}');
                window.history.replaceState(null, null, url);

                // Store in localStorage for client-side persistence
                localStorage.setItem('theme', '{theme}');

                // Update icon
                const themeIcon = document.querySelector('.theme-icon');
                if (themeIcon) {{
                    themeIcon.textContent = '{theme}' === 'dark' ? '☀️' : '🌙';
                }}

                // Update hidden input
                const themeInput = document.getElementById('theme-input');
                if (themeInput) {{
                    themeInput.value = '{theme}';
                }}

                console.log('Theme switched to: {theme}');
            </script>''',
            status_code=200
        )

    except Exception as e:
        logger.error("Error switching theme: %s", e)
        return HTMLResponse(content="<script>console.error('Error switching theme');</script>", status_code=500)
