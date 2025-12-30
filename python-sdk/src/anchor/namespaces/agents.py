"""Agents namespace for Anchor SDK: agent registry and lifecycle management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import BaseNamespace


@dataclass
class Agent:
    """Agent record."""

    id: str
    name: str
    status: str = "active"  # "active" | "suspended"
    metadata: Dict[str, Any] = field(default_factory=dict)
    config_version: Optional[str] = None
    data_count: Optional[int] = None
    checkpoint_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create Agent from API response dict."""
        return cls(
            id=data.get("id") or data.get("agent_id", ""),
            name=data.get("name", ""),
            status=data.get("status", "active"),
            metadata=data.get("metadata") or data.get("config") or {},
            config_version=data.get("config_version"),
            data_count=data.get("data_count"),
            checkpoint_count=data.get("checkpoint_count"),
            created_at=(
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at")
                else None
            ),
        )


class AgentsNamespace(BaseNamespace):
    """
    Agent management operations.

    Usage:
        anchor = Anchor(api_key="your-api-key")

        # Create agent
        agent = anchor.agents.create(
            name="support-bot",
            metadata={"environment": "production", "version": "1.0.0"}
        )

        # Lifecycle operations
        agents = anchor.agents.list(status="active")
        agent = anchor.agents.get("agent_a1b2c3...")
        anchor.agents.suspend("agent_a1b2c3...")
        anchor.agents.activate("agent_a1b2c3...")
        anchor.agents.delete("agent_a1b2c3...")
    """

    def create(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Create a new agent.

        Args:
            name: Human-readable agent name
            metadata: Optional key-value metadata

        Returns:
            Created Agent object
        """
        response = self._http.post(
            "/agents",
            data={
                "name": name,
                "metadata": metadata or {},
            },
        )
        agent_data = response.get("agent", response)
        return Agent.from_dict(agent_data)

    def get(self, agent_id: str) -> Agent:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID (e.g., "agent_a1b2c3")

        Returns:
            Agent object

        Raises:
            NotFoundError: If agent doesn't exist
        """
        response = self._http.get(f"/agents/{agent_id}")
        agent_data = response.get("agent", response)
        return Agent.from_dict(agent_data)

    def list(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Agent]:
        """
        List agents.

        Args:
            status: Filter by status ("active", "suspended")
            limit: Max results (default 50)
            offset: Pagination offset

        Returns:
            List of Agent objects
        """
        params: Dict[str, Any] = {"limit": min(limit, 100), "offset": offset}
        if status:
            params["status"] = status

        response = self._http.get("/agents", params=params)
        agents_data = response.get("agents", [])
        return [Agent.from_dict(a) for a in agents_data]

    def update(
        self,
        agent_id: str,
        metadata: Dict[str, Any],
    ) -> Agent:
        """
        Update agent metadata.

        Args:
            agent_id: Agent ID
            metadata: New metadata (merged with existing)

        Returns:
            Updated Agent object
        """
        response = self._http.patch(
            f"/agents/{agent_id}",
            data={
                "metadata": metadata,
            },
        )
        agent_data = response.get("agent", response)
        return Agent.from_dict(agent_data)

    def delete(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if deleted
        """
        self._http.delete(f"/agents/{agent_id}")
        return True

    def suspend(self, agent_id: str) -> Agent:
        """
        Suspend an agent. Suspended agents cannot perform operations.

        Args:
            agent_id: Agent ID

        Returns:
            Updated Agent object
        """
        response = self._http.post(f"/agents/{agent_id}/suspend")
        agent_data = response.get("agent", response)
        return Agent.from_dict(agent_data)

    def activate(self, agent_id: str) -> Agent:
        """
        Activate a suspended agent.

        Args:
            agent_id: Agent ID

        Returns:
            Updated Agent object
        """
        response = self._http.post(f"/agents/{agent_id}/activate")
        agent_data = response.get("agent", response)
        return Agent.from_dict(agent_data)
