"""Configuration for Anchor SDK."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """
    Configuration for the Anchor client.

    Usage:
        from anchorai import Anchor, Config

        config = Config(
            api_key="your-api-key",
            base_url="https://api.getanchor.dev",
            timeout=30.0,
            retry_attempts=3
        )
        anchor = Anchor(config=config)
    """

    api_key: str
    base_url: str = "https://api.getanchor.dev"
    region: Optional[str] = None
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_size: int = 100
    cache_policies: bool = True
    verify_ssl: bool = True
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate and normalize configuration."""
        self.base_url = self.base_url.rstrip("/")

        # Handle regional endpoints
        if self.region and "api.getanchor.dev" in self.base_url:
            self.base_url = f"https://{self.region}.api.getanchor.dev"
