---
description: "Python coding conventions and rules"
applyTo: "**/*.py"
version: "20251123"
lastModified: "2025-11-23"
---

# ============================================================================
# PYTHON CONVENTIONS
# ============================================================================

## Python Version & Compatibility
- **Target Python version: 3.9.6** (all features up to Python 3.9.6 are allowed)
- Use Python 3 exclusively (shebang: `#!/usr/bin/env python3`)

## Style & Formatting
- Follow PEP 8 style guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 120
- Use f-strings for string formatting (Python 3.6+)
- Do not unnecessarily use from __future__ import annotations unless it is required for the code to function.

## Documentation
- Always use English language for all code comments, docstrings, and documentation
- Docstring style: Google

## Logging
- Use logging module for output (logging.debug, logging.info, logging.warning, logging.error, logging.fatal)
- Use logging sparingly and purposefully.
- Use info only for essential high-level events.
- Use debug rarely, only in places where it provides clear diagnostic value.
- Use warning for situations that should not normally happen, but are not caused by an error in this application.
- Use error when the issue originates from this application, the code should not have reached this point, and the log is needed to identify and fix the problem.
- Always use old-style string formatting with %s and arguments, not f-strings or string concatenation.
  - Correct: logger.info("Processing item %s", item_id)
  - Incorrect: logger.info(f"Processing item {item_id}")
