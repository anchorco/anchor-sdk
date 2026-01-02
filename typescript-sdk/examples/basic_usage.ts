/**
 * Basic usage examples for Anchor TypeScript SDK
 *
 * These examples demonstrate the 5-namespace API:
 * 1. agents     - Agent registry and lifecycle
 * 2. config     - Agent configuration with versioning
 * 3. data       - Governed key-value storage (policy-checked, audit-logged)
 * 4. checkpoints - State snapshots and rollback
 * 5. audit      - Hash-chained audit trail
 */

import { Anchor, DefaultPolicyPack } from 'anchorai';

// Initialize the Anchor client
const anchor = new Anchor({ apiKey: 'your-api-key' }); // Or set ANCHOR_API_KEY env var


async function exampleAgentLifecycle() {
  /** Example: Create and manage an agent */
  console.log('+-+-+- Agent Lifecycle -+-+-+\n');

  // Create an agent
  const agent = await anchor.agents.create('support-bot', {
    environment: 'production',
    version: '1.0',
  });
  console.log(`Created agent: ${agent.id}`);

  // Get agent details
  const fetched = await anchor.agents.get(agent.id);
  console.log(`Agent status: ${fetched?.status}`);

  // List active agents
  const agents = await anchor.agents.list({ status: 'active' });
  console.log(`Active agents: ${agents.length}`);

  // Suspend and reactivate
  await anchor.agents.suspend(agent.id);
  console.log('Agent suspended');

  await anchor.agents.activate(agent.id);
  console.log('Agent reactivated');

  // Update metadata
  await anchor.agents.update(agent.id, { version: '1.1' });
  console.log('Agent metadata updated');
}


async function exampleConfig() {
  /**
   * Example: Agent configuration with versioning
   *
   * Anchor uses a schema-less config approach:
   * - Store ANY fields you want (framework-specific, custom, etc.)
   * - Anchor ONLY enforces the `policies` section
   * - Compatible with any AI framework (CrewAI, LangChain, OpenAI, etc.)
   *
   * The `policies` section is Anchor's core value prop - governance rules
   * that are enforced on every data.write() call.
   */
  console.log('\n+-+-+- Agent Configuration -+-+-+\n');

  const agent = await anchor.agents.create('support-bot');

  // Example 1: OpenAI Assistants style config
  await anchor.config.update(agent.id, {
    instructions: 'You are a helpful customer support agent',
    model: 'gpt-4',
    tools: ['search', 'calculator'],

    // Anchor enforces this
    policies: {
      block_pii: true,
      block_secrets: true,
      retention_days: 90,
    },
  });
  console.log('OpenAI-style config set');

  // Example 2: CrewAI style config
  await anchor.config.update(agent.id, {
    role: 'Customer Support Specialist',
    goal: 'Help customers resolve billing issues quickly',
    backstory: 'You are a senior support agent with 5 years experience',

    // Anchor enforces this
    policies: {
      block_pii: true,
      block_secrets: true,
      retention_days: 30,
      allowed_key_prefixes: ['user:', 'session:', 'pref:'],
    },
  });
  console.log('CrewAI-style config set');

  // Example 3: Custom config with full policy options
  await anchor.config.update(agent.id, {
    // Your custom fields - Anchor just stores these
    my_custom_setting: 'value',
    feature_flags: { new_ui: true },
    max_retries: 3,

    // Anchor enforces these policies on data.write()
    policies: {
      block_pii: true,
      block_secrets: true,
      custom_blocked_patterns: [
        { name: 'internal_id', regex: 'INTERNAL-\\d{6}' },
        { name: 'project_code', regex: 'PROJ-[A-Z]{3}-\\d+' },
      ],
      retention_days: 90,
      retention_by_prefix: {
        'temp:': 1,
        'session:': 7,
      },
      allowed_key_prefixes: ['user:', 'pref:', 'session:'],
      max_value_size_bytes: 10000,
      max_keys_per_agent: 1000,
    },
  });
  console.log('Custom config with full policies set');

  // Get current config
  const config = await anchor.config.get(agent.id);
  console.log(`Current config version: ${config.version}`);
  console.log(`Config keys: ${Object.keys(config.config).join(', ')}`);

  // List config versions
  const versions = await anchor.config.versions(agent.id);
  console.log(`\nConfig versions: ${versions.length}`);
  for (const v of versions) {
    console.log(`  ${v.version}: ${v.createdAt}`);
  }

  // Rollback to previous version
  if (versions.length > 1) {
    await anchor.config.rollback(agent.id, versions[1].version);
    console.log('Rolled back to previous config version');
  }
}


async function exampleDataStorage() {
  /** Example: Governed data storage with policy enforcement */
  console.log('\n+-+-+- Data Storage with Policy Enforcement -+-+-+\n');

  const agent = await anchor.agents.create('support-bot');

  // Configure policies first
  await anchor.config.update(agent.id, {
    policies: { block_pii: true, block_secrets: true },
  });

  // Store user preferences (allowed)
  let result = await anchor.data.write(agent.id, 'user:123:language', 'spanish');
  console.log(`Stored language: allowed=${result.allowed}, audit_id=${result.auditId}`);

  result = await anchor.data.write(agent.id, 'user:123:timezone', 'America/Los_Angeles');
  console.log(`Stored timezone: allowed=${result.allowed}`);

  result = await anchor.data.write(agent.id, 'user:123:preference', 'morning meetings');
  console.log(`Stored preference: allowed=${result.allowed}`);

  // Write with metadata
  result = await anchor.data.write(
    agent.id,
    'user:123:topic',
    'billing questions',
    { source: 'conversation', confidence: 0.9 }
  );
  console.log(`Stored with metadata: allowed=${result.allowed}`);

  // Batch write
  const results = await anchor.data.writeBatch(agent.id, {
    'user:123:name': 'John',
    'user:123:plan': 'enterprise',
  });
  console.log(`\nBatch write: ${results.length} items`);

  // Try to store PII (blocked automatically)
  result = await anchor.data.write(agent.id, 'user:123:email', 'john@example.com');
  console.log(`\nTried to store email: allowed=${result.allowed}`);
  console.log(`  Blocked by: ${result.blockedBy}`);

  // Try to store secrets (blocked automatically)
  result = await anchor.data.write(agent.id, 'config:api_key', 'sk-1234567890abcdef');
  console.log(`\nTried to store API key: allowed=${result.allowed}`);
  console.log(`  Blocked by: ${result.blockedBy}`);
}


async function exampleDataRead() {
  /** Example: Reading and searching data */
  console.log('\n+-+-+- Reading Data -+-+-+\n');

  const agent = await anchor.agents.create('support-bot');

  // Write some data
  await anchor.data.write(agent.id, 'user:123:language', 'spanish');
  await anchor.data.write(agent.id, 'user:123:timezone', 'PST');
  await anchor.data.write(agent.id, 'user:123:preference', 'concise answers');

  // Read by key (returns just the value)
  const value = await anchor.data.read(agent.id, 'user:123:language');
  console.log(`Language: ${value}`);

  // Read full entry with metadata
  const entry = await anchor.data.readFull(agent.id, 'user:123:language');
  if (entry) {
    console.log(`Full entry: key=${entry.key}, value=${entry.value}`);
    console.log(`  Created: ${entry.createdAt}`);
  }

  // List keys with prefix
  const keys = await anchor.data.list(agent.id, { prefix: 'user:123:' });
  console.log(`\nKeys with prefix 'user:123:': ${keys.join(', ')}`);

  // Semantic search
  const results = await anchor.data.search(agent.id, 'how to communicate', { limit: 5 });
  console.log('\nSearch results:');
  for (const r of results) {
    console.log(`  ${r.key}: ${r.value} (similarity: ${r.similarity.toFixed(2)})`);
  }
}


async function exampleDataDelete() {
  /** Example: Deleting data */
  console.log('\n+-+-+- Deleting Data -+-+-+\n');

  const agent = await anchor.agents.create('support-bot');

  // Write test data
  await anchor.data.write(agent.id, 'temp:1', 'value1');
  await anchor.data.write(agent.id, 'temp:2', 'value2');
  await anchor.data.write(agent.id, 'temp:3', 'value3');
  await anchor.data.write(agent.id, 'keep:1', 'important');

  // Delete single key
  await anchor.data.delete(agent.id, 'temp:1');
  console.log('Deleted temp:1');

  // Delete by prefix
  const count = await anchor.data.deletePrefix(agent.id, 'temp:');
  console.log(`Deleted ${count} keys with prefix 'temp:'`);

  // Verify keep:1 still exists
  const value = await anchor.data.read(agent.id, 'keep:1');
  console.log(`keep:1 still exists: ${value}`);
}


async function exampleCheckpoints() {
  /** Example: Checkpoint and rollback */
  console.log('\n+-+-+- Checkpoints and Rollback -+-+-+\n');

  const agent = await anchor.agents.create('data-processor');

  // Write initial state
  await anchor.data.write(agent.id, 'task:status', 'ready');
  await anchor.data.write(agent.id, 'task:count', '10');
  console.log('Initial state written');

  // Create checkpoint before risky operation
  const checkpoint = await anchor.checkpoints.create(agent.id, {
    label: 'pre-batch',
    description: 'Before batch import',
  });
  console.log(`Checkpoint created: ${checkpoint.id}`);

  // List checkpoints
  const checkpoints = await anchor.checkpoints.list(agent.id);
  console.log(`Total checkpoints: ${checkpoints.length}`);

  try {
    // Simulate batch operation that fails
    await anchor.data.write(agent.id, 'task:status', 'processing');
    await anchor.data.write(agent.id, 'task:processed', '5');

    throw new Error('Connection lost during import');
  } catch (e) {
    console.log(`\nError: ${(e as Error).message}`);

    // Rollback to checkpoint
    const result = await anchor.checkpoints.restore(agent.id, checkpoint.id);
    console.log(`Restored from checkpoint: ${result.restoredFrom}`);
    console.log(`  Data keys restored: ${result.dataKeysRestored}`);

    // Verify state was restored
    const status = await anchor.data.read(agent.id, 'task:status');
    console.log(`Status after rollback: ${status}`);
  }
}


async function exampleAudit() {
  /** Example: Query and verify the audit trail */
  console.log('\n+-+-+- Audit Trail -+-+-+\n');

  const agent = await anchor.agents.create('support-bot');

  // Do some operations (all are audit-logged)
  await anchor.data.write(agent.id, 'user:123:language', 'spanish');
  await anchor.data.write(agent.id, 'user:123:timezone', 'PST');
  await anchor.data.delete(agent.id, 'user:123:timezone');

  // Query audit events
  const events = await anchor.audit.query(agent.id, { limit: 10 });
  console.log('Recent agent activity:');
  for (const event of events) {
    console.log(`  ${event.timestamp}: ${event.operation} - ${event.result}`);
    console.log(`    Resource: ${event.resource}`);
    console.log(`    Hash: ${event.hash.slice(0, 16)}...`);
  }

  // Filter by operation type
  const writes = await anchor.audit.query(agent.id, {
    operations: ['data.write'],
    limit: 10,
  });
  console.log(`\nWrite operations: ${writes.length}`);

  // Verify hash chain integrity
  const verification = await anchor.audit.verify(agent.id);
  console.log(`\nAudit chain valid: ${verification.valid}`);
  console.log(`Events checked: ${verification.eventsChecked}`);

  // Export for compliance
  const exportResult = await anchor.audit.export(agent.id, {
    format: 'json',
    includeVerification: true,
  });
  console.log(`\nExport ready: ${exportResult.downloadUrl}`);
}


async function exampleAgentLoop() {
  /** Example: Complete agent loop pattern */
  console.log('\n+-+-+- Agent Loop Pattern -+-+-+\n');

  // Setup - store any config fields your agent needs
  const agent = await anchor.agents.create('support-bot');
  await anchor.config.update(agent.id, {
    // Your agent's config (Anchor just stores this)
    instructions: 'Be helpful and concise',
    model: 'gpt-4',

    // Anchor enforces these on every data.write()
    policies: {
      block_pii: true,
      block_secrets: true,
      allowed_key_prefixes: ['user:', 'session:'],
    },
  });

  async function handleMessage(userId: string, message: string): Promise<string> {
    // 1. Get relevant context via semantic search
    const context = await anchor.data.search(agent.id, message, { limit: 5 });
    const contextStr = context.map((c) => `- ${c.key}: ${c.value}`).join('\n');

    // 2. Get user preferences
    const lang = await anchor.data.read(agent.id, `user:${userId}:language`);

    // 3. Build prompt with context
    const prompt = `
User language: ${lang || 'english'}
Known facts:
${contextStr}

User message: ${message}
`;
    console.log(`Prompt built:\n${prompt}`);

    // 4. Call LLM (placeholder)
    const response = '[Response would be generated here]';

    // 5. Store learned facts (policy-enforced, audit-logged)
    if (message.toLowerCase().includes('french')) {
      const result = await anchor.data.write(agent.id, `user:${userId}:language`, 'french');
      if (result.allowed) {
        console.log(`Learned: user speaks french (audit: ${result.auditId})`);
      }
    }

    return response;
  }

  // Simulate: store initial data and handle a message
  await anchor.data.write(agent.id, 'user:456:language', 'spanish');
  await anchor.data.write(agent.id, 'user:456:timezone', 'PST');

  await handleMessage('456', 'I prefer morning meetings');
}

async function exampleDefaultPolicyPack() {
  /** Example: Use DefaultPolicyPack for out of the box policy configuration */
  console.log('\n+-+-+- Default Policy Pack -+-+-+\n');

  const agent = await anchor.agents.create('support-bot');

  // Use DefaultPolicyPack with no customization
  // Enables: PII blocking, Secret blocking, Query size limit, Approval for edit/delete/export actions
  await anchor.config.update(agent.id, new DefaultPolicyPack().getConfig());
  console.log('Applied default safety policies');

  // Customize specific policies
  const customPack = new DefaultPolicyPack({
    blockSecrets: false,
    maxQuerySize: 5000,
  });
  await anchor.config.update(agent.id, customPack.getConfig());
  console.log('Applied customized policies (secrets blocking disabled, larger query limit)');

  // Disable specific policies
  const disabledPack = new DefaultPolicyPack({
    maxQuerySize: null,
  });
  await anchor.config.update(agent.id, disabledPack.getConfig());
  console.log('Applied policies with query limit disabled');
}

// Main execution
async function main() {
  console.log('Anchor TypeScript SDK Examples');
  console.log('='.repeat(50));
  console.log('\n5-Namespace API:');
  console.log('  anchor.agents      - Agent registry and lifecycle');
  console.log('  anchor.config      - Configuration with versioning');
  console.log('  anchor.data        - Governed key-value storage');
  console.log('  anchor.checkpoints - Snapshots and rollback');
  console.log('  anchor.audit       - Hash-chained audit trail');
  console.log();

  // Uncomment to run examples:
  // await exampleAgentLifecycle();
  // await exampleConfig();
  // await exampleDataStorage();
  // await exampleDataRead();
  // await exampleDataDelete();
  // await exampleCheckpoints();
  // await exampleAudit();
  // await exampleAgentLoop();
  // await exampleDefaultPolicyPack();

  console.log('Uncomment examples in main() to run them.');
}

main().catch(console.error);

export {
  exampleAgentLifecycle,
  exampleConfig,
  exampleDataStorage,
  exampleDataRead,
  exampleDataDelete,
  exampleCheckpoints,
  exampleAudit,
  exampleAgentLoop,
  exampleDefaultPolicyPack,
};
