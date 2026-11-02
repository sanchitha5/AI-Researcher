"""
Small helper for formatting Server-Sent Events.

SSE is just plain text over an HTTP response with a specific
format:

    event: <event_name>
    data: <json string>
    <blank line>

The browser's EventSource / fetch-stream reader on the frontend
parses this format automatically.
"""

import json
from typing import Any


def format_sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"
