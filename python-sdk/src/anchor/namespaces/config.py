"""Config namespace for agent configuration management."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from .base import BaseNamespace


@dataclass
class Config:
    """Agent configuration with versioning."""

    agent_id: str
    version: str
    config: Dict[str, Any]
    previous_version: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    audit_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            agent_id=data.get("agent_id", ""),
            version=data.get("version", ""),
            config=data.get("config", {}),
            previous_version=data.get("previous_version"),
            created_at=(
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at")
                else None
            ),
            created_by=data.get("created_by"),
            audit_id=data.get("audit_id"),
        )


@dataclass
class ConfigVersion:
    """Config version summary."""

    version: str
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    summary: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigVersion":
        return cls(
            version=data.get("version", ""),
            created_at=(
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at")
                else None
            ),
            created_by=data.get("created_by"),
            summary=data.get("summary"),
        )


class ConfigNamespace(BaseNamespace):
    """Agent configuration management with versioning."""

    def get(self, agent_id: str) -> Config:
        """
        Get current config for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Current Config object
        """
        response = self._http.get(f"/agents/{agent_id}/config")
        return Config.from_dict(response)

    def update(self, agent_id: str, config: Dict[str, Any]) -> Config:
        """
        Update agent config. Creates a new version.

        Args:
            agent_id: Agent ID
            config: Config object with behavior, persistence, policies

        Returns:
            New Config object with version

        Example:
            anchor.config.update(agent_id, {
                "behavior": {
                    "instructions": "You are helpful",
                    "constraints": ["Be professional"]
                },
                "policies": {
                    "block_pii": True,
                    "retention_days": 90
                }
            })
        """
        response = self._http.put(f"/agents/{agent_id}/config", data=config)
        return Config.from_dict(response)

    def versions(self, agent_id: str, limit: int = 20) -> List[ConfigVersion]:
        """
        List config versions.

        Args:
            agent_id: Agent ID
            limit: Max versions to return

        Returns:
            List of ConfigVersion objects
        """
        response = self._http.get(
            f"/agents/{agent_id}/config/versions", params={"limit": limit}
        )
        return [ConfigVersion.from_dict(v) for v in response.get("versions", [])]

    def get_version(self, agent_id: str, version: str) -> Config:
        """
        Get a specific config version.

        Args:
            agent_id: Agent ID
            version: Version string (e.g., "v3")

        Returns:
            Config object for that version
        """
        response = self._http.get(f"/agents/{agent_id}/config/versions/{version}")
        return Config.from_dict(response)

    def rollback(self, agent_id: str, target_version: str) -> Config:
        """
        Rollback config to a previous version.
        Creates a new version with the old config.

        Args:
            agent_id: Agent ID
            target_version: Version to rollback to

        Returns:
            New Config object (copy of target version)
        """
        response = self._http.post(
            f"/agents/{agent_id}/config/rollback",
            data={"target_version": target_version},
        )
        return Config.from_dict(response)
