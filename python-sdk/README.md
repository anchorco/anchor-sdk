# Anchor Python SDK

Control what your AI agents store. Audit everything.

## Installation

```bash
pip install anchorai
```

## Quick Start

```python
from anchor import Anchor

anchor = Anchor(api_key="your-api-key")

# Create an agent
agent = anchor.agents.create("support-bot", metadata={"environment": "production"})

# Configure policies
anchor.config.update(agent.id, {
    "policies": {
        "block_pii": True,
        "block_secrets": True,
        "retention_days": 90
    }
})

# Store data (policy-checked, audit-logged)
result = anchor.data.write(agent.id, "user:123:preference", "dark_mode")
print(result.allowed)  # True

# PII is blocked automatically
result = anchor.data.write(agent.id, "user:123:ssn", "123-45-6789")
print(result.allowed)     # False
print(result.blocked_by)  # "policy:block_pii"

# Verify audit chain integrity
verification = anchor.audit.verify(agent.id)
print(verification.valid)  # True
```

## Why Anchor?

- **Policy enforcement**: Block PII, secrets, and custom patterns before storage
- **Checkpoints & rollback**: Snapshot state, restore if something goes wrong
- **Audit trail**: Hash-chained log of every operation, queryable and verifiable
- **Retention policies**: Auto-expire data after N days 

## SDK Structure

The SDK has 5 namespaces:

| Namespace | Purpose |
|-----------|---------|
| `anchor.agents` | Agent registry and lifecycle |
| `anchor.config` | Agent configuration with versioning |
| `anchor.data` | Governed key-value data storage |
| `anchor.checkpoints` | State snapshots and rollback |
| `anchor.audit` | Hash-chained audit trail |

## Agents

```python
# Create agent
agent = anchor.agents.create("my-agent", metadata={"env": "prod"})

# Get agent
agent = anchor.agents.get(agent.id)

# List agents
agents = anchor.agents.list(status="active")

# Update metadata
agent = anchor.agents.update(agent.id, metadata={"version": "2.0"})

# Suspend/Activate
anchor.agents.suspend(agent.id)
anchor.agents.activate(agent.id)

# Delete
anchor.agents.delete(agent.id)
```

## Configuration

Store any config fields you want. Anchor only enforces the `policies` section:

```python
# Get current config
config = anchor.config.get(agent.id)

# Update config - store any fields, Anchor enforces `policies`
anchor.config.update(agent.id, {
    "instructions": "You are a helpful assistant",  # Your field
    "model": "gpt-4",                               # Your field
    "policies": {                                   # Anchor enforces this
        "block_pii": True,
        "block_secrets": True,
        "retention_days": 90,
        "retention_by_prefix": {"temp:": 1, "session:": 7}
    }
})

# Config versioning
versions = anchor.config.versions(agent.id)
old_config = anchor.config.get_version(agent.id, "v1")
anchor.config.rollback(agent.id, "v1")
```

## Data Storage

Policy-enforced key-value storage:

```python
# Write data (policy-checked)
result = anchor.data.write(agent.id, "user:123:preference", "dark_mode")
if result.allowed:
    print(f"Stored with audit_id: {result.audit_id}")
else:
    print(f"Blocked by: {result.blocked_by}")

# Write with metadata
result = anchor.data.write(
    agent.id,
    "user:123:topic",
    "billing questions",
    metadata={"source": "conversation", "confidence": 0.9}
)

# Batch write
results = anchor.data.write_batch(agent.id, [
    {"key": "user:123:name", "value": "John"},
    {"key": "user:123:plan", "value": "enterprise"}
])

# Read data
value = anchor.data.read(agent.id, "user:123:preference")

# Read with metadata
entry = anchor.data.read_full(agent.id, "user:123:preference")
print(entry.value, entry.created_at, entry.metadata)

# Search (text similarity matching)
results = anchor.data.search(agent.id, "user preferences", limit=10)
for r in results:
    print(f"{r.key}: {r.value} (similarity: {r.similarity})")

# List keys
keys = anchor.data.list(agent.id, prefix="user:123:")

# Delete
anchor.data.delete(agent.id, "user:123:preference")
anchor.data.delete_prefix(agent.id, "user:123:")
```

## Checkpoints

Snapshot state and rollback if something goes wrong:

```python
# Create checkpoint before risky operation
checkpoint = anchor.checkpoints.create(agent.id, label="pre-migration")

try:
    for item in large_dataset:
        anchor.data.write(agent.id, item.key, item.value)
except Exception:
    # Something went wrong - restore previous state
    result = anchor.checkpoints.restore(agent.id, checkpoint.id)
    print(f"Restored {result.data_keys_restored} keys")

# List checkpoints
checkpoints = anchor.checkpoints.list(agent.id)

# Get/delete checkpoint
cp = anchor.checkpoints.get(agent.id, checkpoint.id)
anchor.checkpoints.delete(agent.id, checkpoint.id)
```

## Audit Trail

Hash-chained audit logging for compliance and debugging:

```python
# Query audit events
events = anchor.audit.query(
    agent.id,
    operations=["data.write", "data.delete"],
    limit=100
)

for event in events:
    print(f"{event.timestamp}: {event.operation} on {event.resource}")
    print(f"  Result: {event.result}")  # "allowed" or "blocked"
    print(f"  Hash: {event.hash}")

# Verify chain integrity (detects tampering)
verification = anchor.audit.verify(agent.id)
print(verification.valid)          # True if chain intact
print(verification.events_checked) # Number of events verified

# Export for compliance
export = anchor.audit.export(agent.id, format="json")
print(export.download_url)
```

## Framework Integrations

Anchor integrates with popular AI frameworks:

```bash
pip install anchorai[langchain]  # LangChain
pip install anchorai[crewai]     # CrewAI
pip install anchorai[mem0]       # Mem0
pip install anchorai[all]        # All integrations
```

```python
# LangChain - Policy-checked memory
from anchor.integrations.langchain import AnchorMemory

memory = AnchorMemory(anchor=anchor, agent_id=agent.id)
# Use with LangChain chains/agents

# CrewAI - Policy-checked shared memory
from anchor.integrations.crewai import AnchorCrewMemory

memory = AnchorCrewMemory(anchor=anchor)
# Use with CrewAI crews

# Mem0 - Policy-checked memory operations
from anchor.integrations.mem0 import AnchorMem0
from mem0 import Memory

wrapped = AnchorMem0(anchor=anchor, agent_id=agent.id, mem0_client=Memory())
result = wrapped.add("User prefers dark mode", user_id="user_123")
print(result.allowed)  # True or False based on policies
```

## Error Handling

```python
from anchor import (
    AnchorError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    PolicyViolationError,
    RateLimitError
)

try:
    result = anchor.data.write(agent.id, "key", "value")
except PolicyViolationError as e:
    print(f"Blocked: {e.message}")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Agent not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
```

## Client Configuration

```python
from anchor import Anchor

# Simple
anchor = Anchor(api_key="your-api-key")

# Full configuration
anchor = Anchor(
    api_key="your-api-key",
    base_url="https://api.getanchor.dev",
    timeout=30.0,
    retry_attempts=3
)
```

## Requirements

- Python 3.8+
- requests >= 2.28.0

## License

Apache 2.0
