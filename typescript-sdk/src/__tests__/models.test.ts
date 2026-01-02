/**
 * Tests for data models and parsing functions.
 */

/// <reference types="jest" />

import { Anchor } from '../anchor';
import type {
  Agent,
  Config,
  ConfigVersion,
  WriteResult,
  DataEntry,
  SearchResult,
  DataSnapshot,
  Checkpoint,
  RestoreResult,
  AuditEvent,
  Verification,
  ExportResult,
} from '../namespaces';
import { DefaultPolicyPack } from '../policies';

// Mock fetch globally
global.fetch = jest.fn();

// Disable telemetry in tests
process.env.ANCHOR_TELEMETRY = '0';

describe('Agent Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse agent with all fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {
          id: 'agent_123',
          name: 'test-agent',
          status: 'active',
          metadata: { env: 'test', version: '1.0' },
          config_version: 'v5',
          data_count: 100,
          checkpoint_count: 5,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-15T12:30:00Z',
        },
      }),
    } as Response);

    const agent = await anchor.agents.create('test-agent');

    expect(agent.id).toBe('agent_123');
    expect(agent.name).toBe('test-agent');
    expect(agent.status).toBe('active');
    expect(agent.metadata).toEqual({ env: 'test', version: '1.0' });
    expect(agent.configVersion).toBe('v5');
    expect(agent.dataCount).toBe(100);
    expect(agent.checkpointCount).toBe(5);
    expect(agent.createdAt).toBeInstanceOf(Date);
    expect(agent.updatedAt).toBeInstanceOf(Date);
  });

  it('should parse agent with minimal fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {
          id: 'agent_123',
          name: 'test-agent',
          status: 'active',
        },
      }),
    } as Response);

    const agent = await anchor.agents.create('test-agent');

    expect(agent.id).toBe('agent_123');
    expect(agent.name).toBe('test-agent');
    expect(agent.metadata).toEqual({});
    expect(agent.configVersion).toBeUndefined();
    expect(agent.dataCount).toBeUndefined();
    expect(agent.checkpointCount).toBeUndefined();
    expect(agent.createdAt).toBeUndefined();
  });

  it('should parse datetime strings correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {
          id: 'agent_123',
          name: 'test-agent',
          status: 'active',
          created_at: '2024-06-15T14:30:45.123Z',
          updated_at: '2024-06-15T14:30:45.123Z',
        },
      }),
    } as Response);

    const agent = await anchor.agents.create('test-agent');

    expect(agent.createdAt).toBeInstanceOf(Date);
    expect(agent.createdAt?.getFullYear()).toBe(2024);
    expect(agent.createdAt?.getMonth()).toBe(5); // June (0-indexed)
    expect(agent.createdAt?.getDate()).toBe(15);
  });
});

describe('Config Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse config with all fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent_id: 'agent_123',
        version: 'v3',
        config: {
          instructions: 'Be helpful',
          model: 'gpt-4',
          policies: { block_pii: true, block_secrets: true },
        },
        previous_version: 'v2',
        created_at: '2024-01-01T00:00:00Z',
        created_by: 'user_123',
        audit_id: 'audit_abc',
      }),
    } as Response);

    const config = await anchor.config.get('agent_123');

    expect(config.agentId).toBe('agent_123');
    expect(config.version).toBe('v3');
    expect(config.config.instructions).toBe('Be helpful');
    expect(config.config.policies.block_pii).toBe(true);
    expect(config.previousVersion).toBe('v2');
    expect(config.createdAt).toBeInstanceOf(Date);
    expect(config.createdBy).toBe('user_123');
    expect(config.auditId).toBe('audit_abc');
  });

  it('should parse config with minimal fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent_id: 'agent_123',
        version: 'v1',
        config: {},
      }),
    } as Response);

    const config = await anchor.config.get('agent_123');

    expect(config.agentId).toBe('agent_123');
    expect(config.version).toBe('v1');
    expect(config.config).toEqual({});
    expect(config.previousVersion).toBeUndefined();
    expect(config.createdBy).toBeUndefined();
    expect(config.auditId).toBeUndefined();
  });
});

describe('ConfigVersion Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse config versions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        versions: [
          {
            version: 'v3',
            created_at: '2024-01-03T00:00:00Z',
            created_by: 'user_123',
            summary: 'Updated policies',
          },
          {
            version: 'v2',
            created_at: '2024-01-02T00:00:00Z',
            created_by: 'user_456',
            summary: 'Initial config',
          },
        ],
      }),
    } as Response);

    const versions = await anchor.config.versions('agent_123');

    expect(versions).toHaveLength(2);
    expect(versions[0].version).toBe('v3');
    expect(versions[0].createdAt).toBeInstanceOf(Date);
    expect(versions[0].createdBy).toBe('user_123');
    expect(versions[0].summary).toBe('Updated policies');
  });

  it('should handle config versions with minimal fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        versions: [{ version: 'v1' }],
      }),
    } as Response);

    const versions = await anchor.config.versions('agent_123');

    expect(versions[0].version).toBe('v1');
    expect(versions[0].createdBy).toBeUndefined();
    expect(versions[0].summary).toBeUndefined();
  });
});

describe('WriteResult Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse allowed write result', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'user:123:preference',
        allowed: true,
        audit_id: 'audit_123',
        created_at: '2024-01-01T00:00:00Z',
      }),
    } as Response);

    const result = await anchor.data.write('agent_123', 'user:123:preference', 'dark_mode');

    expect(result.key).toBe('user:123:preference');
    expect(result.allowed).toBe(true);
    expect(result.auditId).toBe('audit_123');
    expect(result.blockedBy).toBeUndefined();
    expect(result.reason).toBeUndefined();
  });

  it('should parse blocked write result', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'user:123:email',
        allowed: false,
        audit_id: 'audit_456',
        blocked_by: 'pii_filter',
        reason: 'Email addresses are blocked',
      }),
    } as Response);

    const result = await anchor.data.write('agent_123', 'user:123:email', 'user@example.com');

    expect(result.key).toBe('user:123:email');
    expect(result.allowed).toBe(false);
    expect(result.blockedBy).toBe('pii_filter');
    expect(result.reason).toBe('Email addresses are blocked');
  });

  it('should parse write result with expiration', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'session:abc',
        allowed: true,
        audit_id: 'audit_789',
        expires_at: '2024-01-02T00:00:00Z',
      }),
    } as Response);

    const result = await anchor.data.write('agent_123', 'session:abc', 'data');

    expect(result.expiresAt).toBeInstanceOf(Date);
  });
});

describe('DataEntry Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse full data entry', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'user:123:preference',
        value: 'dark_mode',
        metadata: { source: 'api', confidence: 0.95 },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T00:00:00Z',
        expires_at: '2025-01-01T00:00:00Z',
        audit_id: 'audit_123',
      }),
    } as Response);

    const entry = await anchor.data.readFull('agent_123', 'user:123:preference');

    expect(entry).not.toBeNull();
    expect(entry?.key).toBe('user:123:preference');
    expect(entry?.value).toBe('dark_mode');
    expect(entry?.metadata).toEqual({ source: 'api', confidence: 0.95 });
    expect(entry?.createdAt).toBeInstanceOf(Date);
    expect(entry?.updatedAt).toBeInstanceOf(Date);
    expect(entry?.expiresAt).toBeInstanceOf(Date);
    expect(entry?.auditId).toBe('audit_123');
  });

  it('should parse data entry with minimal fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'user:123:preference',
        value: 'dark_mode',
        audit_id: 'audit_123',
      }),
    } as Response);

    const entry = await anchor.data.readFull('agent_123', 'user:123:preference');

    expect(entry?.metadata).toEqual({});
    expect(entry?.expiresAt).toBeUndefined();
  });
});

describe('SearchResult Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse search results', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        results: [
          { key: 'user:123:lang', value: 'spanish', similarity: 0.95, metadata: { source: 'api' } },
          { key: 'user:456:lang', value: 'french', similarity: 0.87, metadata: {} },
        ],
      }),
    } as Response);

    const results = await anchor.data.search('agent_123', 'language preference');

    expect(results).toHaveLength(2);
    expect(results[0].key).toBe('user:123:lang');
    expect(results[0].value).toBe('spanish');
    expect(results[0].similarity).toBe(0.95);
    expect(results[0].metadata).toEqual({ source: 'api' });
  });

  it('should handle search result with minimal fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        results: [{ key: 'test', value: 'data', similarity: 0.8 }],
      }),
    } as Response);

    const results = await anchor.data.search('agent_123', 'query');

    expect(results[0].metadata).toEqual({});
  });
});

describe('Checkpoint Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse checkpoint with all fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        id: 'cp_123',
        agent_id: 'agent_123',
        label: 'pre-migration',
        description: 'Checkpoint before database migration',
        config_version: 'v5',
        data_snapshot: { key_count: 100, total_size_bytes: 10240 },
        created_at: '2024-01-01T00:00:00Z',
        audit_id: 'audit_xyz',
      }),
    } as Response);

    const checkpoint = await anchor.checkpoints.create('agent_123', { label: 'pre-migration' });

    expect(checkpoint.id).toBe('cp_123');
    expect(checkpoint.agentId).toBe('agent_123');
    expect(checkpoint.label).toBe('pre-migration');
    expect(checkpoint.description).toBe('Checkpoint before database migration');
    expect(checkpoint.configVersion).toBe('v5');
    expect(checkpoint.dataSnapshot.keyCount).toBe(100);
    expect(checkpoint.dataSnapshot.totalSizeBytes).toBe(10240);
    expect(checkpoint.createdAt).toBeInstanceOf(Date);
    expect(checkpoint.auditId).toBe('audit_xyz');
  });

  it('should parse checkpoint with minimal fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        id: 'cp_123',
        agent_id: 'agent_123',
        config_version: 'v1',
        data_snapshot: {},
      }),
    } as Response);

    const checkpoint = await anchor.checkpoints.create('agent_123');

    expect(checkpoint.label).toBeUndefined();
    expect(checkpoint.description).toBeUndefined();
    expect(checkpoint.dataSnapshot.keyCount).toBe(0);
    expect(checkpoint.dataSnapshot.totalSizeBytes).toBe(0);
    expect(checkpoint.auditId).toBeUndefined();
  });
});

describe('RestoreResult Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse restore result with all fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        restored_from: 'cp_123',
        config_restored: true,
        config_version: 'v5',
        data_restored: true,
        data_keys_restored: 100,
        data_keys_removed: 25,
        audit_id: 'audit_restore',
        restored_at: '2024-01-15T00:00:00Z',
      }),
    } as Response);

    const result = await anchor.checkpoints.restore('agent_123', 'cp_123');

    expect(result.restoredFrom).toBe('cp_123');
    expect(result.configRestored).toBe(true);
    expect(result.configVersion).toBe('v5');
    expect(result.dataRestored).toBe(true);
    expect(result.dataKeysRestored).toBe(100);
    expect(result.dataKeysRemoved).toBe(25);
    expect(result.auditId).toBe('audit_restore');
    expect(result.restoredAt).toBeInstanceOf(Date);
  });

  it('should parse restore result with partial restore', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        restored_from: 'cp_123',
        config_restored: false,
        data_restored: true,
        data_keys_restored: 50,
        data_keys_removed: 0,
        audit_id: 'audit_partial',
      }),
    } as Response);

    const result = await anchor.checkpoints.restore('agent_123', 'cp_123', { restoreConfig: false });

    expect(result.configRestored).toBe(false);
    expect(result.dataRestored).toBe(true);
  });
});

describe('AuditEvent Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse audit event with all fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        events: [
          {
            id: 'audit_123',
            agent_id: 'agent_123',
            operation: 'data.write',
            resource: 'user:123:preference',
            result: 'allowed',
            blocked_by: null,
            timestamp: '2024-01-01T12:00:00Z',
            hash: 'abc123def456',
            previous_hash: 'xyz789',
            metadata: { source: 'api', user_id: 'user_456' },
          },
        ],
      }),
    } as Response);

    const events = await anchor.audit.query('agent_123');

    expect(events).toHaveLength(1);
    expect(events[0].id).toBe('audit_123');
    expect(events[0].agentId).toBe('agent_123');
    expect(events[0].operation).toBe('data.write');
    expect(events[0].resource).toBe('user:123:preference');
    expect(events[0].result).toBe('allowed');
    expect(events[0].blockedBy).toBeFalsy(); // null or undefined
    expect(events[0].timestamp).toBeInstanceOf(Date);
    expect(events[0].hash).toBe('abc123def456');
    expect(events[0].previousHash).toBe('xyz789');
    expect(events[0].metadata).toEqual({ source: 'api', user_id: 'user_456' });
  });

  it('should parse blocked audit event', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        events: [
          {
            id: 'audit_456',
            agent_id: 'agent_123',
            operation: 'data.write',
            resource: 'user:123:email',
            result: 'blocked',
            blocked_by: 'pii_filter',
            hash: 'blocked_hash',
          },
        ],
      }),
    } as Response);

    const events = await anchor.audit.query('agent_123');

    expect(events[0].result).toBe('blocked');
    expect(events[0].blockedBy).toBe('pii_filter');
  });

  it('should parse audit event with no previous hash (first in chain)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        events: [
          {
            id: 'audit_first',
            agent_id: 'agent_123',
            operation: 'agent.create',
            resource: 'agent_123',
            result: 'allowed',
            hash: 'first_hash',
            previous_hash: null,
          },
        ],
      }),
    } as Response);

    const events = await anchor.audit.query('agent_123');

    expect(events[0].previousHash).toBeFalsy(); // null or undefined
  });
});

describe('Verification Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse valid verification result', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        valid: true,
        events_checked: 1000,
        chain_start: 'hash_start',
        chain_end: 'hash_end',
        verified_at: '2024-01-01T00:00:00Z',
        first_invalid: null,
      }),
    } as Response);

    const verification = await anchor.audit.verify('agent_123');

    expect(verification.valid).toBe(true);
    expect(verification.eventsChecked).toBe(1000);
    expect(verification.chainStart).toBe('hash_start');
    expect(verification.chainEnd).toBe('hash_end');
    expect(verification.verifiedAt).toBeInstanceOf(Date);
    expect(verification.firstInvalid).toBeFalsy(); // null or undefined
  });

  it('should parse invalid verification result', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        valid: false,
        events_checked: 500,
        chain_start: 'hash_start',
        chain_end: null,
        verified_at: '2024-01-01T00:00:00Z',
        first_invalid: { id: 'audit_500', expected_hash: 'abc', actual_hash: 'xyz' },
      }),
    } as Response);

    const verification = await anchor.audit.verify('agent_123');

    expect(verification.valid).toBe(false);
    expect(verification.eventsChecked).toBe(500);
    expect(verification.firstInvalid).toEqual({
      id: 'audit_500',
      expected_hash: 'abc',
      actual_hash: 'xyz',
    });
  });
});

describe('ExportResult Model', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should parse export result with verification', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        export_id: 'exp_123',
        format: 'json',
        download_url: 'https://api.getanchor.dev/exports/exp_123',
        expires_at: '2024-01-02T00:00:00Z',
        event_count: 1000,
        verification: {
          valid: true,
          events_checked: 1000,
          verified_at: '2024-01-01T00:00:00Z',
        },
      }),
    } as Response);

    const result = await anchor.audit.export('agent_123', { includeVerification: true });

    expect(result.exportId).toBe('exp_123');
    expect(result.format).toBe('json');
    expect(result.downloadUrl).toBe('https://api.getanchor.dev/exports/exp_123');
    expect(result.expiresAt).toBeInstanceOf(Date);
    expect(result.eventCount).toBe(1000);
    expect(result.verification).toBeDefined();
    expect(result.verification?.valid).toBe(true);
    expect(result.verification?.eventsChecked).toBe(1000);
  });

  it('should parse export result without verification', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        export_id: 'exp_456',
        format: 'csv',
        download_url: 'https://api.getanchor.dev/exports/exp_456',
        expires_at: '2024-01-02T00:00:00Z',
        event_count: 500,
      }),
    } as Response);

    const result = await anchor.audit.export('agent_123', { format: 'csv', includeVerification: false });

    expect(result.format).toBe('csv');
    expect(result.verification).toBeUndefined();
  });
});

describe('Model Edge Cases', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let anchor: Anchor;

  beforeEach(() => {
    mockFetch.mockClear();
    anchor = new Anchor({ apiKey: 'anc_test_key' });
  });

  it('should handle empty arrays', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ agents: [] }),
    } as Response);

    const agents = await anchor.agents.list();
    expect(agents).toEqual([]);
  });

  it('should handle missing optional fields gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {},
      }),
    } as Response);

    const agent = await anchor.agents.create('test');

    expect(agent.id).toBe('');
    expect(agent.name).toBe('');
    expect(agent.status).toBe('active');
    expect(agent.metadata).toEqual({});
  });

  it('should handle batch write results', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        results: [
          { key: 'key1', allowed: true, audit_id: 'audit_1' },
          { key: 'key2', allowed: false, audit_id: 'audit_2', blocked_by: 'pii_filter' },
          { key: 'key3', allowed: true, audit_id: 'audit_3' },
        ],
      }),
    } as Response);

    const results = await anchor.data.writeBatch('agent_123', {
      key1: 'value1',
      key2: 'value2',
      key3: 'value3',
    });

    expect(results).toHaveLength(3);
    expect(results[0].allowed).toBe(true);
    expect(results[1].allowed).toBe(false);
    expect(results[1].blockedBy).toBe('pii_filter');
    expect(results[2].allowed).toBe(true);
  });

  it('should handle list checkpoints', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        checkpoints: [
          { id: 'cp_1', agent_id: 'agent_123', config_version: 'v1', data_snapshot: {} },
          { id: 'cp_2', agent_id: 'agent_123', config_version: 'v2', data_snapshot: { key_count: 50 } },
        ],
      }),
    } as Response);

    const checkpoints = await anchor.checkpoints.list('agent_123');

    expect(checkpoints).toHaveLength(2);
    expect(checkpoints[0].id).toBe('cp_1');
    expect(checkpoints[1].dataSnapshot.keyCount).toBe(50);
  });
});

describe('DefaultPolicyPack', () => {
  it('should have correct defaults', () => {
    const pack = new DefaultPolicyPack();
    const config = pack.getConfig();
    const policies = config.policies;

    expect(policies.max_query_size).toBe(1000);
    expect(policies.allowed_domains).toBeUndefined();
    expect(policies.require_approval_for).toEqual(['delete', 'update', 'export']);
    expect(policies.block_pii).toBe(true);
    expect(policies.block_secrets).toBe(true);
  });

  it('should allow custom values', () => {
    const pack = new DefaultPolicyPack({
      allowedDomains: ['example.com'],
      maxQuerySize: 500,
      requireApprovalFor: ['delete'],
      blockPii: false,
      blockSecrets: false,
    });
    const config = pack.getConfig();
    const policies = config.policies;

    expect(policies.allowed_domains).toEqual(['example.com']);
    expect(policies.max_query_size).toBe(500);
    expect(policies.require_approval_for).toEqual(['delete']);
    expect(policies.block_pii).toBe(false);
    expect(policies.block_secrets).toBe(false);
  });

  it('should allow disabling optional policies', () => {
    const pack = new DefaultPolicyPack({
      allowedDomains: null,
      maxQuerySize: null,
      requireApprovalFor: null,
    });
    const config = pack.getConfig();
    const policies = config.policies;

    expect(policies.allowed_domains).toBeUndefined();
    expect(policies.max_query_size).toBeUndefined();
    expect(policies.require_approval_for).toBeUndefined();
    expect(policies.block_pii).toBe(true);
    expect(policies.block_secrets).toBe(true);
  });
});
