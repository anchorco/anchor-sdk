# Anchor TypeScript SDK

Control what your AI agents store. Audit everything.

## Installation

```bash
npm install anchorai
```

## Quick Start

### 1. Get Your Credentials

Sign up at [getanchor.dev](https://getanchor.dev) to get:
- **API Key** (e.g., `your-api-key`)
- **Workspace ID** (e.g., `your-workspace-id`)

### 2. Install the SDK

```bash
npm install anchorai
```

### 3. Initialize and Use

```typescript
import { Anchor } from 'anchorai';

// Initialize with your API key and workspace ID
const anchor = new Anchor({ 
  apiKey: 'your-api-key',
  workspaceId: 'your-workspace-id'
});

// Create an agent (workspaceId is automatically included)
const agent = await anchor.agents.create('support-bot', { environment: 'production' });

// Configure policies
await anchor.config.update(agent.id, {
  policies: {
    block_pii: true,
    block_secrets: true,
    retention_days: 90
  }
});

// Store data (policy-checked, audit-logged)
const result = await anchor.data.write(agent.id, 'user:123:preference', 'dark_mode');
console.log(result.allowed);  // true

// PII is blocked automatically
const blocked = await anchor.data.write(agent.id, 'user:123:ssn', '123-45-6789');
console.log(blocked.allowed);     // false
console.log(blocked.blockedBy);   // "policy:block_pii"

// Verify audit chain integrity
const verification = await anchor.audit.verify(agent.id);
console.log(verification.valid);  // true
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

```typescript
// Create agent
const agent = await anchor.agents.create('my-agent', { env: 'prod' });

// Get agent
const fetched = await anchor.agents.get(agent.id);

// List agents
const agents = await anchor.agents.list({ status: 'active' });

// Update metadata
const updated = await anchor.agents.update(agent.id, { version: '2.0' });

// Suspend/Activate
await anchor.agents.suspend(agent.id);
await anchor.agents.activate(agent.id);

// Delete
await anchor.agents.delete(agent.id);
```

## Configuration

Store any config fields you want. Anchor only enforces the `policies` section:

```typescript
// Get current config
const config = await anchor.config.get(agent.id);

// Update config - store any fields, Anchor enforces `policies`
await anchor.config.update(agent.id, {
  instructions: 'You are a helpful assistant',  // Your field
  model: 'gpt-4',                               // Your field
  policies: {                                   // Anchor enforces this
    block_pii: true,
    block_secrets: true,
    retention_days: 90,
    retention_by_prefix: { 'temp:': 1, 'session:': 7 }
  }
});

// Config versioning
const versions = await anchor.config.versions(agent.id);
const oldConfig = await anchor.config.getVersion(agent.id, 'v1');
await anchor.config.rollback(agent.id, 'v1');
```

## Data Storage

Policy-enforced key-value storage:

```typescript
// Write data (policy-checked)
const result = await anchor.data.write(agent.id, 'user:123:preference', 'dark_mode');
if (result.allowed) {
  console.log(`Stored with audit_id: ${result.auditId}`);
} else {
  console.log(`Blocked by: ${result.blockedBy}`);
}

// Write with metadata
const result2 = await anchor.data.write(
  agent.id,
  'user:123:topic',
  'billing questions',
  { source: 'conversation', confidence: 0.9 }
);

// Batch write
const results = await anchor.data.writeBatch(agent.id, {
  'user:123:name': 'John',
  'user:123:plan': 'enterprise'
});

// Read data
const value = await anchor.data.read(agent.id, 'user:123:preference');

// Read with metadata
const entry = await anchor.data.readFull(agent.id, 'user:123:preference');
console.log(entry?.value, entry?.createdAt, entry?.metadata);

// Search (text similarity matching)
const results = await anchor.data.search(agent.id, 'user preferences', { limit: 10 });
for (const r of results) {
  console.log(`${r.key}: ${r.value} (similarity: ${r.similarity})`);
}

// List keys
const keys = await anchor.data.list(agent.id, { prefix: 'user:123:' });

// Delete
await anchor.data.delete(agent.id, 'user:123:preference');
await anchor.data.deletePrefix(agent.id, 'user:123:');
```

## Checkpoints

Snapshot state and rollback if something goes wrong:

```typescript
// Create checkpoint before risky operation
const checkpoint = await anchor.checkpoints.create(agent.id, { label: 'pre-migration' });

try {
  for (const item of largeDataset) {
    await anchor.data.write(agent.id, item.key, item.value);
  }
} catch (error) {
  // Something went wrong - restore previous state
  const result = await anchor.checkpoints.restore(agent.id, checkpoint.id);
  console.log(`Restored ${result.dataKeysRestored} keys`);
}

// List checkpoints
const checkpoints = await anchor.checkpoints.list(agent.id);

// Get/delete checkpoint
const cp = await anchor.checkpoints.get(agent.id, checkpoint.id);
await anchor.checkpoints.delete(agent.id, checkpoint.id);
```

## Audit Trail

Hash-chained audit logging for compliance and debugging:

```typescript
// Query audit events
const events = await anchor.audit.query(agent.id, {
  operations: ['data.write', 'data.delete'],
  limit: 100
});

for (const event of events) {
  console.log(`${event.timestamp}: ${event.operation} on ${event.resource}`);
  console.log(`  Result: ${event.result}`);  // "allowed" or "blocked"
  console.log(`  Hash: ${event.hash}`);
}

// Verify chain integrity (detects tampering)
const verification = await anchor.audit.verify(agent.id);
console.log(verification.valid);          // true if chain intact
console.log(verification.eventsChecked);  // Number of events verified

// Export for compliance
const exportResult = await anchor.audit.export(agent.id, { format: 'json' });
console.log(exportResult.downloadUrl);
```

## Framework Integrations

Anchor integrates with popular AI frameworks:

```typescript
// LangChain - Policy-checked memory
import { AnchorMemory } from 'anchorai';

const memory = new AnchorMemory(anchor, agent.id);
// Use with LangChain chains/agents

// CrewAI - Policy-checked shared memory
import { AnchorCrewMemory } from 'anchorai';

const memory = new AnchorCrewMemory(anchor);
// Use with CrewAI crews

// Mem0 - Policy-checked memory operations
import { AnchorMem0 } from 'anchorai';

const wrapped = new AnchorMem0(anchor, agent.id, mem0Client);
const result = await wrapped.add('User prefers dark mode', { userId: 'user_123' });
console.log(result.allowed);  // true or false based on policies
```

## Error Handling

```typescript
import {
  AnchorError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  PolicyViolationError,
  RateLimitError
} from 'anchorai';

try {
  const result = await anchor.data.write(agent.id, 'key', 'value');
} catch (error) {
  if (error instanceof PolicyViolationError) {
    console.log(`Blocked: ${error.message}`);
  } else if (error instanceof AuthenticationError) {
    console.log('Invalid API key');
  } else if (error instanceof NotFoundError) {
    console.log('Agent not found');
  } else if (error instanceof RateLimitError) {
    console.log(`Rate limited. Retry after ${error.retryAfter}s`);
  }
}
```

## Client Configuration

```typescript
import { Anchor } from 'anchorai';

// Simple
const anchor = new Anchor({ apiKey: 'your-api-key' });

// Full configuration
const anchor = new Anchor({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.getanchor.dev',
  timeout: 30000,
  retryAttempts: 3
});
```

## Requirements

- Node.js 18+
- TypeScript 4.5+

## License

Apache 2.0
