"""
Basic usage examples for Anchor Python SDK

These examples demonstrate the 5-namespace API:
1. agents     - Agent registry and lifecycle
2. config     - Agent configuration with versioning
3. data       - Governed key-value storage (policy-checked, audit-logged)
4. checkpoints - State snapshots and rollback
5. audit      - Hash-chained audit trail
"""

from anchor import Anchor, DefaultPolicyPack

# Initialize the Anchor client
anchor = Anchor(api_key="your-api-key")  # Or set ANCHOR_API_KEY env var


def example_agent_lifecycle():
    """Example: Create and manage an agent"""
    print("+-+-+- Agent Lifecycle -+-+-+\n")

    # Create an agent
    agent = anchor.agents.create(
        name="support-bot",
        metadata={"environment": "production", "version": "1.0"}
    )
    print(f"Created agent: {agent.id}")

    # Get agent details
    fetched = anchor.agents.get(agent.id)
    print(f"Agent status: {fetched.status}")

    # List active agents
    agents = anchor.agents.list(status="active")
    print(f"Active agents: {len(agents)}")

    # Suspend and reactivate
    anchor.agents.suspend(agent.id)
    print("Agent suspended")

    anchor.agents.activate(agent.id)
    print("Agent reactivated")

    # Update metadata
    anchor.agents.update(agent.id, metadata={"version": "1.1"})
    print("Agent metadata updated")


def example_config():
    """Example: Agent configuration with versioning

    Anchor uses a schema-less config approach:
    - Store ANY fields you want (framework-specific, custom, etc.)
    - Anchor ONLY enforces the `policies` section
    - Compatible with any AI framework (CrewAI, LangChain, OpenAI, etc.)

    The `policies` section is Anchor's core value prop - governance rules
    that are enforced on every data.write() call:
       - block_pii: bool                  # Block emails, SSNs, phones
       - block_secrets: bool              # Block API keys, passwords, tokens
       - custom_blocked_patterns: [{name, regex}]
       - retention_days: int              # Auto-delete after N days
       - retention_by_prefix: {prefix: days}
       - allowed_key_prefixes: [str]      # Whitelist
       - denied_key_prefixes: [str]       # Blacklist
       - max_value_size_bytes: int
       - max_keys_per_agent: int
    """
    print("\n+-+-+- Agent Configuration -+-+-+\n")

    agent = anchor.agents.create(name="support-bot")

    # Example 1: OpenAI Assistants style config
    anchor.config.update(agent.id, {
        "instructions": "You are a helpful customer support agent",
        "model": "gpt-4",
        "tools": ["search", "calculator"],

        # Anchor enforces this
        "policies": {
            "block_pii": True,
            "block_secrets": True,
            "retention_days": 90
        }
    })
    print("OpenAI-style config set")

    # Example 2: CrewAI style config
    anchor.config.update(agent.id, {
        "role": "Customer Support Specialist",
        "goal": "Help customers resolve billing issues quickly",
        "backstory": "You are a senior support agent with 5 years experience",

        # Anchor enforces this
        "policies": {
            "block_pii": True,
            "block_secrets": True,
            "retention_days": 30,
            "allowed_key_prefixes": ["user:", "session:", "pref:"]
        }
    })
    print("CrewAI-style config set")

    # Example 3: Custom config with full policy options
    anchor.config.update(agent.id, {
        # Your custom fields - Anchor just stores these
        "my_custom_setting": "value",
        "feature_flags": {"new_ui": True},
        "max_retries": 3,

        # Anchor enforces these policies on data.write()
        "policies": {
            "block_pii": True,           # Block emails, SSNs, phones
            "block_secrets": True,       # Block API keys, passwords
            "custom_blocked_patterns": [  # Your custom patterns
                {"name": "internal_id", "regex": r"INTERNAL-\d{6}"},
                {"name": "project_code", "regex": r"PROJ-[A-Z]{3}-\d+"}
            ],
            "retention_days": 90,        # Auto-delete after 90 days
            "retention_by_prefix": {
                "temp:": 1,              # Temp data: 1 day
                "session:": 7            # Session data: 7 days
            },
            "allowed_key_prefixes": [    # Only allow these prefixes
                "user:",
                "pref:",
                "session:"
            ],
            "max_value_size_bytes": 10000,
            "max_keys_per_agent": 1000
        }
    })
    print("Custom config with full policies set")

    # Get current config
    config = anchor.config.get(agent.id)
    print(f"Current config version: {config.version}")
    print(f"Config keys: {list(config.config.keys())}")

    # List config versions
    versions = anchor.config.versions(agent.id)
    print(f"\nConfig versions: {len(versions)}")
    for v in versions:
        print(f"  {v.version}: {v.created_at}")

    # Rollback to previous version
    if len(versions) > 1:
        anchor.config.rollback(agent.id, versions[1].version)
        print("Rolled back to previous config version")


def example_default_policy_pack():
    """Example: Use DefaultPolicyPack for out of the box policy configuration"""
    print("\n+-+-+- Default Policy Pack -+-+-+\n")

    agent = anchor.agents.create(name="default-policy-pack-demo")

    # Use DefaultPolicyPack for out of the box policy configuration
    # Enables: PII blocking, Secret blocking, Query size limit, Approval for edit/delete/export actions
    anchor.config.update(agent.id, DefaultPolicyPack().get_config())
    print("Applied default safety policies")

    # Customize specific policies
    custom_pack = DefaultPolicyPack(block_secrets=False, max_query_size=5000)
    anchor.config.update(agent.id, custom_pack.get_config())
    print("Applied customized policies (secrets allowed, larger query limit)")

    # Disable specific policies by setting to None
    # e.g. Disable max_query_size limit entirely
    disabled_policy_pack = DefaultPolicyPack(max_query_size=None)
    anchor.config.update(agent.id, disabled_policy_pack.get_config())
    print("Applied policies with query limit disabled")


def example_data_storage():
    """Example: Governed data storage with policy enforcement"""
    print("\n+-+-+- Data Storage with Policy Enforcement -+-+-+\n")

    agent = anchor.agents.create(name="support-bot")

    # Configure policies first
    anchor.config.update(agent.id, {
        "policies": {"block_pii": True, "block_secrets": True}
    })

    # Store user preferences (allowed)
    result = anchor.data.write(agent.id, "user:123:language", "spanish")
    print(f"Stored language: allowed={result.allowed}, audit_id={result.audit_id}")

    result = anchor.data.write(agent.id, "user:123:timezone", "America/Los_Angeles")
    print(f"Stored timezone: allowed={result.allowed}")

    result = anchor.data.write(agent.id, "user:123:preference", "morning meetings")
    print(f"Stored preference: allowed={result.allowed}")

    # Write with metadata
    result = anchor.data.write(
        agent.id,
        "user:123:topic",
        "billing questions",
        metadata={"source": "conversation", "confidence": 0.9}
    )
    print(f"Stored with metadata: allowed={result.allowed}")

    # Batch write
    results = anchor.data.write_batch(agent.id, {
        "user:123:name": "John",
        "user:123:plan": "enterprise"
    })
    print(f"\nBatch write: {len(results)} items")


def example_data_read():
    """Example: Reading and searching data"""
    print("\n+-+-+- Reading Data -+-+-+\n")

    agent = anchor.agents.create(name="support-bot")

    # Write some data
    anchor.data.write(agent.id, "user:123:language", "spanish")
    anchor.data.write(agent.id, "user:123:timezone", "PST")
    anchor.data.write(agent.id, "user:123:preference", "concise answers")

    # Read by key (returns just the value)
    value = anchor.data.read(agent.id, "user:123:language")
    print(f"Language: {value}")

    # Read full entry with metadata
    entry = anchor.data.read_full(agent.id, "user:123:language")
    if entry:
        print(f"Full entry: key={entry.key}, value={entry.value}")
        print(f"  Created: {entry.created_at}")

    # List keys with prefix
    keys = anchor.data.list(agent.id, prefix="user:123:")
    print(f"\nKeys with prefix 'user:123:': {keys}")

    # Semantic search
    results = anchor.data.search(agent.id, "how to communicate", limit=5)
    print(f"\nSearch results:")
    for r in results:
        print(f"  {r.key}: {r.value} (similarity: {r.similarity:.2f})")


def example_data_delete():
    """Example: Deleting data"""
    print("\n+-+-+- Deleting Data -+-+-+\n")

    agent = anchor.agents.create(name="support-bot")

    # Write test data
    anchor.data.write(agent.id, "temp:1", "value1")
    anchor.data.write(agent.id, "temp:2", "value2")
    anchor.data.write(agent.id, "temp:3", "value3")
    anchor.data.write(agent.id, "keep:1", "important")

    # Delete single key
    anchor.data.delete(agent.id, "temp:1")
    print("Deleted temp:1")

    # Delete by prefix
    count = anchor.data.delete_prefix(agent.id, "temp:")
    print(f"Deleted {count} keys with prefix 'temp:'")

    # Verify keep:1 still exists
    value = anchor.data.read(agent.id, "keep:1")
    print(f"keep:1 still exists: {value}")


def example_checkpoints():
    """Example: Checkpoint and rollback"""
    print("\n+-+-+- Checkpoints and Rollback -+-+-+\n")

    agent = anchor.agents.create(name="data-processor")

    # Write initial state
    anchor.data.write(agent.id, "task:status", "ready")
    anchor.data.write(agent.id, "task:count", "10")
    print("Initial state written")

    # Create checkpoint before risky operation
    checkpoint = anchor.checkpoints.create(
        agent.id,
        label="pre-batch",
        description="Before batch import"
    )
    print(f"Checkpoint created: {checkpoint.id}")

    # List checkpoints
    checkpoints = anchor.checkpoints.list(agent.id)
    print(f"Total checkpoints: {len(checkpoints)}")

    try:
        # Simulate batch operation that fails
        anchor.data.write(agent.id, "task:status", "processing")
        anchor.data.write(agent.id, "task:processed", "5")

        raise Exception("Connection lost during import")

    except Exception as e:
        print(f"\nError: {e}")

        # Rollback to checkpoint
        result = anchor.checkpoints.restore(agent.id, checkpoint.id)
        print(f"Restored from checkpoint: {result.restored_from}")
        print(f"  Data keys restored: {result.data_keys_restored}")

        # Verify state was restored
        status = anchor.data.read(agent.id, "task:status")
        print(f"Status after rollback: {status}")


def example_audit():
    """Example: Query and verify the audit trail"""
    print("\n+-+-+- Audit Trail -+-+-+\n")

    agent = anchor.agents.create(name="support-bot")

    # Do some operations (all are audit-logged)
    anchor.data.write(agent.id, "user:123:language", "spanish")
    anchor.data.write(agent.id, "user:123:timezone", "PST")
    anchor.data.delete(agent.id, "user:123:timezone")

    # Query audit events
    events = anchor.audit.query(agent.id, limit=10)
    print("Recent agent activity:")
    for event in events:
        print(f"  {event.timestamp}: {event.operation} - {event.result}")
        print(f"    Resource: {event.resource}")
        print(f"    Hash: {event.hash[:16]}...")

    # Filter by operation type
    writes = anchor.audit.query(
        agent.id,
        operations=["data.write"],
        limit=10
    )
    print(f"\nWrite operations: {len(writes)}")

    # Verify hash chain integrity
    verification = anchor.audit.verify(agent.id)
    print(f"\nAudit chain valid: {verification.valid}")
    print(f"Events checked: {verification.events_checked}")

    # Export for compliance
    export = anchor.audit.export(
        agent.id,
        format="json",
        include_verification=True
    )
    print(f"\nExport ready: {export.download_url}")


def example_agent_loop():
    """Example: Complete agent loop pattern"""
    print("\n+-+-+- Agent Loop Pattern -+-+-+\n")

    # Setup - store any config fields your agent needs
    agent = anchor.agents.create(name="support-bot")
    anchor.config.update(agent.id, {
        # Your agent's config (Anchor just stores this)
        "instructions": "Be helpful and concise",
        "model": "gpt-4",

        # Anchor enforces these on every data.write()
        "policies": {
            "block_pii": True,
            "block_secrets": True,
            "allowed_key_prefixes": ["user:", "session:"]
        }
    })

    def handle_message(user_id: str, message: str) -> str:
        # 1. Get relevant context via semantic search
        context = anchor.data.search(agent.id, message, limit=5)
        context_str = "\n".join([f"- {c.key}: {c.value}" for c in context])

        # 2. Get user preferences
        lang = anchor.data.read(agent.id, f"user:{user_id}:language")

        # 3. Build prompt with context
        prompt = f"""
User language: {lang or 'english'}
Known facts:
{context_str}

User message: {message}
"""
        print(f"Prompt built:\n{prompt}")

        # 4. Call LLM (placeholder)
        response = "[Response would be generated here]"

        # 5. Store learned facts (policy-enforced, audit-logged)
        if "french" in message.lower():
            result = anchor.data.write(agent.id, f"user:{user_id}:language", "french")
            if result.allowed:
                print(f"Learned: user speaks french (audit: {result.audit_id})")

        return response

    # Simulate: store initial data and handle a message
    anchor.data.write(agent.id, "user:456:language", "spanish")
    anchor.data.write(agent.id, "user:456:timezone", "PST")

    handle_message("456", "I prefer morning meetings")


if __name__ == "__main__":
    print("Anchor Python SDK Examples")
    print("=" * 50)
    print("\n5-Namespace API:")
    print("  anchor.agents      - Agent registry and lifecycle")
    print("  anchor.config      - Configuration with versioning")
    print("  anchor.data        - Governed key-value storage")
    print("  anchor.checkpoints - Snapshots and rollback")
    print("  anchor.audit       - Hash-chained audit trail")
    print()

    # Uncomment to run examples:
    # example_agent_lifecycle()
    # example_config()
    # example_data_storage()
    # example_data_read()
    # example_data_delete()
    # example_checkpoints()
    # example_audit()
    # example_agent_loop()

    print("Uncomment examples in main() to run them.")
