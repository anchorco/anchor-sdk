"""Anonymous telemetry for Anchor SDK

Tracks SDK usage to help improve the product. Completely opt-out, transparent, and privacy-respecting.
"""

import os
import platform
import sys
import threading
import time
from typing import Optional, Dict, Any
import requests

# Telemetry endpoint (can be overridden via env var)
TELEMETRY_ENDPOINT = os.getenv(
    "ANCHOR_TELEMETRY_ENDPOINT", "https://api.getanchor.dev/telemetry"
)

# Check if telemetry is disabled
TELEMETRY_ENABLED = os.getenv("ANCHOR_TELEMETRY", "1").lower() not in (
    "0",
    "false",
    "off",
    "no",
    "disabled",
)


class Telemetry:
    """Anonymous telemetry tracker for SDK usage"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.enabled = TELEMETRY_ENABLED
        self.session = requests.Session()
        self.session.timeout = 2  # Short timeout, don't block

        # SDK metadata
        self.sdk_version = "1.0.0"
        self.language = "python"
        self.language_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.platform = platform.system()
        self.platform_version = platform.release()

        # Track initialization
        if self.enabled:
            self._track_async(
                "sdk.initialized",
                {
                    "sdk_version": self.sdk_version,
                    "language": self.language,
                    "language_version": self.language_version,
                    "platform": self.platform,
                    "platform_version": self.platform_version,
                    "has_api_key": bool(api_key),
                },
            )

    def _track_async(self, event: str, properties: Optional[Dict[str, Any]] = None):
        """Track an event asynchronously (non-blocking)"""
        if not self.enabled:
            return

        def send_event():
            try:
                payload = {
                    "event": event,
                    "properties": properties or {},
                    "sdk_version": self.sdk_version,
                    "language": self.language,
                    "timestamp": int(time.time() * 1000),
                }

                # Don't send API key or any sensitive data
                # Only send base_url domain (not full URL)
                if self.base_url:
                    try:
                        from urllib.parse import urlparse

                        parsed = urlparse(self.base_url)
                        payload["base_url_domain"] = parsed.netloc or "localhost"
                    except Exception:
                        pass

                self.session.post(
                    TELEMETRY_ENDPOINT,
                    json=payload,
                    timeout=2,
                    headers={"User-Agent": f"anchor-sdk-python/{self.sdk_version}"},
                )
            except Exception:
                # Silently fail - never interrupt user experience
                pass

        # Send in background thread
        thread = threading.Thread(target=send_event, daemon=True)
        thread.start()

    def track_method_call(
        self, method_name: str, success: bool = True, error_type: Optional[str] = None
    ):
        """Track a method call"""
        if not self.enabled:
            return

        properties = {"method": method_name, "success": success}

        if error_type:
            properties["error_type"] = error_type

        self._track_async("sdk.method_called", properties)

    def track_error(self, error_type: str, method_name: Optional[str] = None):
        """Track an error"""
        if not self.enabled:
            return

        properties = {"error_type": error_type}

        if method_name:
            properties["method"] = method_name

        self._track_async("sdk.error", properties)


# Global telemetry instance (created per client)
_telemetry_instances: Dict[str, Telemetry] = {}


def get_telemetry(base_url: str, api_key: Optional[str] = None) -> Telemetry:
    """Get or create telemetry instance for a client"""
    key = f"{base_url}:{api_key or 'no-key'}"
    if key not in _telemetry_instances:
        _telemetry_instances[key] = Telemetry(base_url, api_key)
    return _telemetry_instances[key]
