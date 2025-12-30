"""
Anchor Mem0 Integration.

Adds policy enforcement, persistent storage, audit trails, and checkpoint/rollback to Mem0.

Anchor works ABOVE Mem0:
- Mem0 answers "what does the agent remember?"
- Anchor answers "what is the agent allowed to remember, and can you prove it?"

Usage:
    from anchor import Anchor
    from anchor.integrations.mem0 import AnchorMem0
    from mem0 import Memory

    anchor = Anchor(api_key="your-api-key")
    agent = anchor.agents.create("mem0-agent")

    # Configure policies
    anchor.config.update(agent.id, {
        "policies": {"block_pii": True, "retention_days": 90}
    })

    # Wrap Mem0 with policy enforcement
    mem0_client = Memory()
    wrapped = AnchorMem0(
        anchor=anchor,
        agent_id=agent.id,
        mem0_client=mem0_client
    )

    # Policy enforcement
    result = wrapped.add("User email is john@example.com", user_id="user_123")
    if not result.allowed:
        print(f"Blocked: {result.blocked_by}")

    # Checkpoint & rollback
    checkpoint_id = wrapped.create_checkpoint(label="before-batch")
    # wrapped.restore_checkpoint(checkpoint_id)  # if needed

    # Audit trail
    events = anchor.audit.query(agent.id, limit=10)
    verification = anchor.audit.verify(agent.id)  # Verify chain integrity
"""

from typing import Any, List, Optional, Dict
from dataclasses import dataclass

# Check for Mem0 availability
try:
    from mem0 import Memory

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    Memory = None


@dataclass
class PolicyResult:
    """Result of a policy-checked operation."""

    allowed: bool
    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    mem0_result: Any = None
    expires_at: Optional[Any] = None  # datetime when data will auto-delete (if retention policy set)

    def __bool__(self) -> bool:
        return self.allowed


class AnchorMem0:
    """
    Policy-enforced Mem0 wrapper with persistent storage, audit trails, and checkpoints.

    Wraps a Mem0 Memory instance to add:
    - Policy checks before write operations
    - Automatic audit logging
    - PII/secrets blocking

    Usage:
        from anchor import Anchor
        from anchor.integrations.mem0 import AnchorMem0
        from mem0 import Memory

        anchor = Anchor(api_key="your-api-key")
        agent = anchor.agents.create(name="mem0-agent")

        # Configure policies
        anchor.config.update(agent.id, {
            "policies": {"block_pii": True, "block_secrets": True}
        })

        mem0_client = Memory()
        wrapped = AnchorMem0(
            anchor=anchor,
            agent_id=agent.id,
            mem0_client=mem0_client
        )

        # Operations are policy-checked
        result = wrapped.add("User prefers dark mode", user_id="user_123")
        if result.allowed:
            print("Stored successfully")
        else:
            print(f"Blocked by: {result.blocked_by}")
    """

    def __init__(self, anchor: Any, agent_id: str, mem0_client: Any):
        """
        Initialize AnchorMem0.

        Args:
            anchor: Anchor client instance
            agent_id: Anchor agent identifier
            mem0_client: Mem0 Memory instance
        """
        if not MEM0_AVAILABLE:
            raise ImportError("Mem0 is required. Install with: pip install mem0ai")

        self.anchor = anchor
        self.agent_id = agent_id
        self.mem0 = mem0_client

    def add(
        self,
        data: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> PolicyResult:
        """
        Add memory with policy enforcement. Data persists across restarts.

        Args:
            data: Memory content
            user_id: User identifier
            agent_id: Mem0 agent identifier (not Anchor agent)
            run_id: Run identifier
            metadata: Additional metadata
            **kwargs: Additional Mem0 options

        Returns:
            PolicyResult with allowed status and expiration info (expires_at if retention set)
        """
        # Check policy by attempting to write to Anchor
        key = f"mem0:{user_id or 'unknown'}:{agent_id or 'default'}"
        write_result = self.anchor.data.write(
            self.agent_id,
            key,
            data,
            metadata={"source": "mem0", "user_id": user_id, "run_id": run_id},
        )

        if not write_result.allowed:
            return PolicyResult(
                allowed=False,
                blocked_by=write_result.blocked_by,
                reason=write_result.reason,
                mem0_result=None,
                expires_at=None,
            )

        # If allowed, call Mem0
        result = self.mem0.add(
            data=data,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            metadata=metadata,
            **kwargs,
        )

        # Return with expiration info from Anchor
        return PolicyResult(
            allowed=True, 
            blocked_by=None, 
            reason=None, 
            mem0_result=result,
            expires_at=write_result.expires_at,  # Include expiration date
        )

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 10,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Search memories (not blocked, but audit-logged).

        Args:
            query: Search query
            user_id: User identifier
            agent_id: Mem0 agent identifier
            run_id: Run identifier
            limit: Maximum results
            **kwargs: Additional Mem0 options

        Returns:
            List of matching memories
        """
        # Log the search operation
        self.anchor.data.write(
            self.agent_id,
            f"mem0:search:{user_id or 'unknown'}",
            query[:200],
            metadata={"type": "search", "user_id": user_id},
        )

        return self.mem0.search(
            query=query,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            limit=limit,
            **kwargs,
        )

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory or None if not found
        """
        return self.mem0.get(memory_id)

    def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories.

        Args:
            user_id: Filter by user
            agent_id: Filter by Mem0 agent
            run_id: Filter by run
            **kwargs: Additional Mem0 options

        Returns:
            List of memories
        """
        return self.mem0.get_all(
            user_id=user_id, agent_id=agent_id, run_id=run_id, **kwargs
        )

    def update(self, memory_id: str, data: str, **kwargs) -> PolicyResult:
        """
        Update a memory with policy enforcement.

        Args:
            memory_id: Memory identifier
            data: New memory content
            **kwargs: Additional Mem0 options

        Returns:
            PolicyResult with allowed status and Mem0 result
        """
        # Check policy
        write_result = self.anchor.data.write(
            self.agent_id,
            f"mem0:update:{memory_id}",
            data,
            metadata={"type": "update", "memory_id": memory_id},
        )

        if not write_result.allowed:
            return PolicyResult(
                allowed=False,
                blocked_by=write_result.blocked_by,
                reason=write_result.reason,
                mem0_result=None,
                expires_at=None,
            )

        # If allowed, call Mem0
        result = self.mem0.update(memory_id=memory_id, data=data, **kwargs)

        return PolicyResult(
            allowed=True, 
            blocked_by=None, 
            reason=None, 
            mem0_result=result,
            expires_at=write_result.expires_at,  # Include expiration date
        )

    def delete(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a memory (audit-logged but not blocked).

        Args:
            memory_id: Memory identifier

        Returns:
            Deletion result
        """
        # Log deletion
        self.anchor.data.write(
            self.agent_id,
            f"mem0:delete:{memory_id}",
            "deleted",
            metadata={"type": "delete", "memory_id": memory_id},
        )

        return self.mem0.delete(memory_id)

    def delete_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delete all memories matching criteria.

        Args:
            user_id: Filter by user
            agent_id: Filter by Mem0 agent
            run_id: Filter by run

        Returns:
            Deletion result
        """
        # Log bulk deletion
        self.anchor.data.write(
            self.agent_id,
            f"mem0:delete_all:{user_id or 'all'}",
            "bulk_delete",
            metadata={"type": "delete_all", "user_id": user_id, "agent_id": agent_id},
        )

        return self.mem0.delete_all(user_id=user_id, agent_id=agent_id, run_id=run_id)

    def history(self, memory_id: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Get memory history.

        Args:
            memory_id: Memory identifier
            **kwargs: Additional options

        Returns:
            List of memory history entries
        """
        return self.mem0.history(memory_id, **kwargs)

    def reset(self) -> Dict[str, Any]:
        """
        Reset all memories.

        Returns:
            Reset result
        """
        # Log reset
        self.anchor.data.write(
            self.agent_id, "mem0:reset", "full_reset", metadata={"type": "reset"}
        )

        return self.mem0.reset()

    def create_checkpoint(self, label: Optional[str] = None) -> str:
        """
        Create a checkpoint of current memory state.

        Args:
            label: Optional label for the checkpoint

        Returns:
            Checkpoint ID

        Example:
            # Create checkpoint before risky operation
            checkpoint_id = wrapped.create_checkpoint(label="before-migration")
            
            # ... perform risky operations ...
            
            # If something goes wrong, restore
            wrapped.restore_checkpoint(checkpoint_id)
        """
        checkpoint = self.anchor.checkpoints.create(
            self.agent_id, label=label or "mem0-checkpoint"
        )
        return checkpoint.id

    def restore_checkpoint(self, checkpoint_id: str) -> None:
        """
        Restore memory to a previous checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore

        Example:
            # Restore to checkpoint after detecting corruption
            wrapped.restore_checkpoint(checkpoint_id)
            print("Memory restored to checkpoint")
        """
        self.anchor.checkpoints.restore(self.agent_id, checkpoint_id)
        # Note: Mem0's internal state may need to be reloaded after restore

    def query_audit_log(
        self,
        operations: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Any]:
        """
        Query audit trail for this agent's operations.

        Args:
            operations: Filter by operation types (e.g., ["data.write"])
            limit: Max events to return

        Returns:
            List of audit events

        Example:
            # See what operations were performed
            events = wrapped.query_audit_log(operations=["data.write"], limit=50)
            for event in events:
                print(f"{event.timestamp}: {event.operation} - {event.result}")
        """
        return self.anchor.audit.query(
            self.agent_id, operations=operations, limit=limit
        )

    def verify_audit_chain(self) -> Any:
        """
        Verify the integrity of the audit chain.

        Returns:
            Verification result with valid status

        Example:
            # Verify logs haven't been tampered with
            verification = wrapped.verify_audit_chain()
            if verification.valid:
                print("Audit chain is intact")
            else:
                print("WARNING: Audit chain integrity compromised!")
        """
        return self.anchor.audit.verify(self.agent_id)

    def export_audit_log(
        self, format: str = "json", include_verification: bool = True
    ) -> Any:
        """
        Export audit trail for compliance.

        Args:
            format: Export format ("json" or "csv")
            include_verification: Include chain verification

        Returns:
            ExportResult with download URL

        Example:
            # Export for compliance review
            export = wrapped.export_audit_log(format="json")
            print(f"Download audit log: {export.download_url}")
        """
        return self.anchor.audit.export(
            self.agent_id, format=format, include_verification=include_verification
        )
