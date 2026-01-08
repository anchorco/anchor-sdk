"""
Anchor: Control what your AI agents store. Audit everything.

Anchor lets you persist agent state, block bad data, prove what happened.

1. Quick Start:
    from anchor import Anchor

    anchor = Anchor(api_key="your-api-key")
    agent = anchor.agents.create("my-agent")

2. Full Example:
    from anchor import Anchor

    anchor = Anchor(api_key="your-api-key")

    # Create agent
    agent = anchor.agents.create(
        name="support-bot",
        metadata={"environment": "production"}
    )

    # Store data (automatically audit-logged)
    anchor.data.write(agent.id, "user:123:pref", "concise answers")
    print(result.allowed)  # True

    # PII gets blocked by policy
    result = anchor.data.write(agent.id, "user:123:ssn", "123-45-6789")
    print(result.allowed)  # False - blocked by policy

    # Checkpoint before risky operation
    checkpoint = anchor.checkpoints.create(agent.id, label="pre-update")

    # Something goes wrong? Rollback
    anchor.checkpoints.restore(agent.id, checkpoint.id)

    # Prove what happened
    events = anchor.audit.query(agent.id, limit=5)
        from anchor import Anchor
"""

from typing import Optional

from .config import Config as ClientConfig
from ._http import HttpClient
from .namespaces import (
    AgentsNamespace,
    ConfigNamespace,
    DataNamespace,
    CheckpointsNamespace,
    AuditNamespace,
)


class Anchor:
    """
    Anchor client for AI agent state management.

    Usage:
        # Simple initialization
        anchor = Anchor(api_key="your-api-key")

        # With configuration
        from anchorai import Anchor, ClientConfig

        config = ClientConfig(
            api_key="your-api-key",
            base_url="https://api.getanchor.dev",
            timeout=30.0,
            retry_attempts=3
        )
        anchor = Anchor(config=config)

    Namespaces:
        anchor.agents       - Agent registry and lifecycle
        anchor.config       - Agent configuration with versioning
        anchor.data         - Governed key-value data storage
        anchor.checkpoints  - State snapshots and rollback
        anchor.audit        - Hash-chained audit trail
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[ClientConfig] = None,
        **kwargs,
    ):
        """
        Initialize Anchor client.

        Args:
            api_key: API key
            workspace_id: Workspace ID (optional, can also be passed per-operation)
            base_url: API base URL (default: https://api.getanchor.dev)
            config: Full configuration object
            **kwargs: Additional configuration options passed to Config
        """
        if config is not None:
            self._config = config
        else:
            if api_key is None:
                raise ValueError("api_key is required")

            self._config = ClientConfig(
                api_key=api_key,
                workspace_id=workspace_id,
                base_url=base_url or "https://api.getanchor.dev",
                **kwargs,
            )

        # Initialize HTTP client
        self._http = HttpClient(self._config)

        # Initialize namespaces (5 per spec)
        self._agents = AgentsNamespace(self._http)
        self._config_ns = ConfigNamespace(self._http)
        self._data = DataNamespace(self._http)
        self._checkpoints = CheckpointsNamespace(self._http)
        self._audit = AuditNamespace(self._http)

    @property
    def agents(self) -> AgentsNamespace:
        """Agent registry and lifecycle management."""
        return self._agents

    @property
    def config(self) -> ConfigNamespace:
        """Agent configuration with versioning."""
        return self._config_ns

    @property
    def data(self) -> DataNamespace:
        """Governed key-value data storage."""
        return self._data

    @property
    def checkpoints(self) -> CheckpointsNamespace:
        """State snapshots and rollback."""
        return self._checkpoints

    @property
    def audit(self) -> AuditNamespace:
        """Hash-chained audit trail."""
        return self._audit

    @property
    def client_config(self) -> ClientConfig:
        """Current client configuration."""
        return self._config

    def get_workspace_id(self) -> Optional[str]:
        """
        Attempt to fetch the default workspace ID for the current API key.
        
        This is a convenience method. If it fails, you should provide workspace_id
        explicitly when initializing Anchor() or get it from the signup flow.
        
        Returns:
            Workspace ID if found, None otherwise
            
        Note:
            This method may not work if the API doesn't expose a /workspaces endpoint.
            In that case, get your workspace_id from the signup page at app.getanchor.dev
        """
        if self._config.workspace_id:
            return self._config.workspace_id
        
        try:
            # Try to fetch workspaces (endpoint may not exist)
            response = self._http.get("/workspaces")
            workspaces = response.get("workspaces", response.get("data", []))
            if isinstance(workspaces, list) and len(workspaces) > 0:
                workspace = workspaces[0]
                return workspace.get("id") or workspace.get("workspaceId")
        except Exception:
            # If endpoint doesn't exist or fails, return None
            pass
        
        return None

    def __repr__(self) -> str:
        return f"Anchor(base_url='{self._config.base_url}')"
