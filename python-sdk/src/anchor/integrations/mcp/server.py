"""
MCP (Model Context Protocol) server integration for Anchor SDK.

This module provides a minimal wrapper for MCP servers to enable
governance capabilities. Implementation is intentionally skeletal
to allow incremental enhancement.
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from anchor import Anchor


class AnchorMCPServer:
    """
    Wrapper for MCP servers that enables Anchor governance.

    This is a minimal integration skeleton.
    Enforcement, auditing, and context handling
    will be added incrementally.

    Args:
        anchor: Anchor SDK instance for governance
        agent_id: ID of the agent using this MCP server
        base_server: The underlying MCP server to wrap
        validate: Whether to validate agent_id exists (default: True)

    Raises:
        ValueError: If validation is enabled and agent_id is invalid

    Example:
        >>> from anchor import Anchor
        >>> from anchor.integrations.mcp import AnchorMCPServer
        >>>
        >>> anchor = Anchor(api_key="your-key")
        >>> agent = anchor.agents.create("mcp-agent")
        >>>
        >>> mcp_server = AnchorMCPServer(
        ...     anchor=anchor,
        ...     agent_id=agent.id,
        ...     base_server=your_mcp_server
        ... )
        >>> mcp_server.start()
    """

    def __init__(
        self,
        anchor: "Anchor",
        agent_id: str,
        base_server: Any,
        validate: bool = True,
    ):
        """
        Initialize the Anchor MCP server wrapper.

        Args:
            anchor: Anchor SDK instance
            agent_id: Agent identifier
            base_server: MCP server instance to wrap
            validate: Whether to validate agent exists (default: True)

        Raises:
            ValueError: If validation enabled and agent_id invalid
        """
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be a non-empty string")

        # Optional validation for better DX and early error detection
        if validate:
            if not hasattr(anchor, "agents"):
                raise ValueError(
                    "anchor instance does not expose agents API. "
                    "Ensure you're using a valid Anchor instance."
                )
            try:
                # Verify agent exists
                anchor.agents.get(agent_id)
            except Exception as e:
                raise ValueError(
                    f"Failed to validate agent_id '{agent_id}': {e}. "
                    "Pass validate=False to skip validation."
                ) from e

        self.anchor = anchor
        self.agent_id = agent_id
        self.base_server = base_server

    def start(self) -> Any:
        """
        Start the wrapped MCP server.

        Currently delegates directly to the base server.
        Future versions will add governance hooks.

        Returns:
            Result from the base server's start method
        """
        return self.base_server.start()
