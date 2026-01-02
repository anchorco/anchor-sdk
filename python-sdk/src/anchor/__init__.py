"""Anchor: Control what your AI agents store. Audit everything.

Anchor lets you persist agent state, block bad data, prove what happened.

1. Quick Start:
    from anchor import Anchor

    anchor = Anchor(api_key="your-api-key")
    agent = anchor.agents.create("my-agent")

2. Full Example:
    from anchor import Anchor

    anchor = Anchor(api_key="your-api-key")

    # Create agent
    agent = anchor.agents.create(name="support-bot")

    # Store data (automatically audit-logged)
    anchor.data.write(agent.id, "user:123:pref", "concise answers")

    # PII gets blocked by policy
    result = anchor.data.write(agent.id, "user:123:ssn", "123-45-6789")
    print(result.allowed)  # False - blocked by policy

    # Checkpoint before risky operation
    checkpoint = anchor.checkpoints.create(agent.id, label="pre-update")

    # Something goes wrong? Rollback
    anchor.checkpoints.restore(agent.id, checkpoint.id)

    # Prove what happened
    events = anchor.audit.query(agent.id, limit=5)
"""

# Main client
from .anchor import Anchor
from .config import Config as ClientConfig

# Exceptions
from .exceptions import (
    AnchorAPIError,
    AnchorError,
    AuthenticationError,
    AuthorizationError,
    ChainIntegrityError,
    NetworkError,
    NotFoundError,
    PolicyViolationError,
    RateLimitError,
    ServerError,
    ValidationError,
)

# Types from namespaces
from .namespaces import (  # Agent types; Config types; Data types; Checkpoint types; Audit types
    Agent,
    AuditEvent,
    Checkpoint,
    Config,
    ConfigVersion,
    DataEntry,
    ExportResult,
    RestoreResult,
    SearchResult,
    Verification,
    WriteResult,
)
from .policies import DefaultPolicyPack

__version__ = "1.0.0"

__all__ = [
    # Main client
    "Anchor",
    "ClientConfig",
    "DefaultPolicyPack",
    # Agent types
    "Agent",
    # Config types
    "Config",
    "ConfigVersion",
    # Data types
    "WriteResult",
    "DataEntry",
    "SearchResult",
    # Checkpoint types
    "Checkpoint",
    "RestoreResult",
    # Audit types
    "AuditEvent",
    "Verification",
    "ExportResult",
    # Exceptions
    "AnchorError",
    "AnchorAPIError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "PolicyViolationError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "ChainIntegrityError",
]
