"""
Anchor CrewAI Integration.

Policy-checked agents, storage, audit trails, and checkpoints for CrewAI multi-agent systems.

Components:
- AnchorCrewAgent: CrewAI agent registered with Anchor
- AnchorCrewMemory: Policy-checked shared memory with checkpoints

Usage:
    from anchor import Anchor
    from anchor.integrations.crewai import AnchorCrewAgent, AnchorCrewMemory
    from crewai import Crew

    anchor = Anchor(api_key="your-api-key")

    # Create agents with Anchor registration
    researcher = AnchorCrewAgent(
        anchor=anchor,
        role="Senior Researcher",
        goal="Find comprehensive information"
    )

    writer = AnchorCrewAgent(
        anchor=anchor,
        role="Content Writer",
        goal="Create engaging content"
    )

    # Create policy-checked shared memory
    memory = AnchorCrewMemory(anchor=anchor)

    # Configure policies
    anchor.config.update(memory.agent_id, {
        "policies": {"block_pii": True, "retention_days": 90}
    })

    crew = Crew(
        agents=[researcher.agent, writer.agent],
        tasks=[...],
        memory=memory
    )

    # Checkpoint & audit
    checkpoint_id = memory.create_checkpoint(label="before-experiment")
    events = anchor.audit.query(memory.agent_id, limit=50)
    verification = anchor.audit.verify(memory.agent_id)  # Verify chain integrity
"""

from typing import Any, List, Optional, Dict

# Check for CrewAI availability
try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None


class AnchorCrewAgent:
    """
    CrewAI agent registered with Anchor.

    Description: Creates a CrewAI agent that is:
    - Registered in Anchor's agent registry
    - Has configurable policies (blocks PII, secrets, custom patterns)
    - Operations are audit-logged (hash-chained, tamper-evident)
    - Can query, verify, and export audit trails

    Usage:
        from anchor import Anchor
        from anchor.integrations.crewai import AnchorCrewAgent

        anchor = Anchor(api_key="your-api-key")

        researcher = AnchorCrewAgent(
            anchor=anchor,
            role="Senior Researcher",
            goal="Find comprehensive information",
            backstory="Expert researcher with 10 years experience"
        )

        # Configure policies for this agent
        anchor.config.update(researcher.agent_id, {
            "behavior": {"instructions": "Be thorough and accurate"},
            "policies": {"block_pii": True, "block_secrets": True}
        })

        # Access the CrewAI agent
        crew_agent = researcher.agent

        # Example: Query audit trail for this agent
        events = anchor.audit.query(researcher.agent_id, operations=["data.write"], limit=50)
        for event in events:
            print(f"{event.timestamp}: {event.operation} - {event.result}")

        # Example: Verify audit chain integrity
        verification = anchor.audit.verify(researcher.agent_id)
        print(f"Audit chain valid: {verification.valid}")
    """

    def __init__(
        self,
        anchor: Any,
        role: str,
        goal: str,
        backstory: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        verbose: bool = False,
        **kwargs,
    ):
        """
        Initialize AnchorCrewAgent.

        Args:
            anchor: Anchor client instance
            role: Agent's role in the crew
            goal: Agent's goal
            backstory: Agent's backstory
            tools: List of tools for the agent
            verbose: Enable verbose output
            **kwargs: Additional CrewAI agent options
        """
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI is required. Install with: pip install crewai")

        self.anchor = anchor
        self.role = role
        self.goal = goal

        # Register agent with Anchor
        self._anchor_agent = anchor.agents.create(
            name=f"crewai-{role.lower().replace(' ', '-')}",
            metadata={"framework": "crewai", "role": role, "goal": goal},
        )

        # Create CrewAI agent
        self._agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory or f"An agent with the role of {role}",
            tools=tools or [],
            verbose=verbose,
            **kwargs,
        )

    @property
    def agent(self) -> Any:
        """Get the underlying CrewAI agent."""
        return self._agent

    @property
    def agent_id(self) -> str:
        """Get the Anchor agent ID."""
        return self._anchor_agent.id

    def store(
        self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store data for this agent (policy-checked).

        Args:
            key: Storage key
            value: Value to store
            metadata: Optional metadata

        Returns:
            True if stored successfully
        """
        result = self.anchor.data.write(
            self._anchor_agent.id, key, value, metadata=metadata
        )
        return result.allowed

    def retrieve(self, key: str) -> Optional[str]:
        """
        Retrieve data for this agent.

        Args:
            key: Storage key

        Returns:
            Value or None if not found
        """
        return self.anchor.data.read(self._anchor_agent.id, key)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search agent's data.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching entries
        """
        results = self.anchor.data.search(self._anchor_agent.id, query, limit=limit)
        return [
            {"key": r.key, "value": r.value, "similarity": r.similarity}
            for r in results
        ]


class AnchorCrewMemory:
    """
    Policy-checked shared memory for CrewAI with persistent storage and checkpoints.

    Description: Provides a memory backend for CrewAI that:
    - Enforces policies (PII blocking, etc.)
    - Logs all operations to audit trail
    - Supports checkpoints and rollback

    Usage:
        from anchor import Anchor
        from anchor.integrations.crewai import AnchorCrewMemory
        from crewai import Crew

        anchor = Anchor(api_key="your-api-key")
        memory = AnchorCrewMemory(anchor=anchor)
        anchor.config.update(memory.agent_id, {
            "policies": {"block_pii": True, "retention_days": 90}
        })
        crew = Crew(agents=[...], tasks=[...], memory=memory)
    """

    def __init__(self, anchor: Any, agent_id: Optional[str] = None):
        """
        Initialize AnchorCrewMemory.

        Args:
            anchor: Anchor client instance
            agent_id: Optional specific agent ID (creates one if not provided)
        """
        self.anchor = anchor

        # Create or use agent
        if agent_id:
            self._agent_id = agent_id
        else:
            agent = anchor.agents.create(
                "crewai-shared-memory",
                metadata={"framework": "crewai", "type": "shared-memory"},
            )
            self._agent_id = agent.id

    @property
    def agent_id(self) -> str:
        """Get the Anchor agent ID."""
        return self._agent_id

    def save(self, key: str, value: Any) -> bool:
        """
        Save a value to memory (policy-checked, persistent storage).

        Args:
            key: Memory key
            value: Value to store

        Returns:
            True if saved successfully (data persists across crew restarts)
        """
        # Convert value to string if needed
        str_value = value if isinstance(value, str) else str(value)

        result = self.anchor.data.write(
            self._agent_id, key, str_value, metadata={"source": "crewai"}
        )
        return result.allowed

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memory.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memories
        """
        results = self.anchor.data.search(self._agent_id, query, limit=limit)
        return [{"key": r.key, "value": r.value} for r in results]

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from memory.

        Args:
            key: Memory key

        Returns:
            Value or None if not found
        """
        return self.anchor.data.read(self._agent_id, key)

    def delete(self, key: str) -> bool:
        """
        Delete a value from memory.

        Args:
            key: Memory key

        Returns:
            True if deleted
        """
        return self.anchor.data.delete(self._agent_id, key)

    def clear(self) -> int:
        """
        Clear all memory.

        Returns:
            Number of keys deleted
        """
        return self.anchor.data.delete_prefix(self._agent_id, "")

    def create_checkpoint(self, label: Optional[str] = None) -> str:
        """
        Create a checkpoint of current memory state.

        Args:
            label: Optional label for the checkpoint

        Returns:
            Checkpoint ID

        Example:
            # Create checkpoint before risky operation
            checkpoint_id = memory.create_checkpoint(label="before-migration")
            
            # ... perform risky operations ...
            
            # If corruption detected, restore
            memory.restore_checkpoint(checkpoint_id)
        """
        checkpoint = self.anchor.checkpoints.create(
            self._agent_id, label=label or "crewai-checkpoint"
        )
        return checkpoint.id

    def restore_checkpoint(self, checkpoint_id: str) -> None:
        """
        Restore memory to a previous checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore

        Example:
            # Restore to checkpoint after detecting corruption
            memory.restore_checkpoint(checkpoint_id)
            print("Memory restored to checkpoint")
        """
        self.anchor.checkpoints.restore(self._agent_id, checkpoint_id)
