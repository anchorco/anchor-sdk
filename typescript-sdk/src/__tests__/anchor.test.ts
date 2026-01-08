/**
 * Tests for Anchor SDK with 5 namespaces (agents, config, data, checkpoints, audit)
 */

/// <reference types="jest" />

import { Anchor } from '../anchor';
import type {
  Agent,
  Config,
  WriteResult,
  Checkpoint,
  AuditEvent,
  Verification,
} from '../namespaces';

// Mock fetch globally
global.fetch = jest.fn();

// Disable telemetry in tests
process.env.ANCHOR_TELEMETRY = '0';

describe('Anchor Client', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('Initialization', () => {
    it('should initialize with API key', () => {
      const anchor = new Anchor({ apiKey: 'anc_test_key' });
      expect(anchor.clientConfig.apiKey).toBe('anc_test_key');
    });

    it('should initialize with workspaceId', () => {
      const anchor = new Anchor({ apiKey: 'anc_test_key', workspaceId: 'workspace-123' });
      expect(anchor.clientConfig.apiKey).toBe('anc_test_key');
      expect(anchor.clientConfig.workspaceId).toBe('workspace-123');
    });

    it('should have all 5 namespaces', () => {
      const anchor = new Anchor({ apiKey: 'anc_test_key' });
      expect(anchor.agents).toBeDefined();
      expect(anchor.config).toBeDefined();
      expect(anchor.data).toBeDefined();
      expect(anchor.checkpoints).toBeDefined();
      expect(anchor.audit).toBeDefined();
    });
  });

  describe('getWorkspaceId', () => {
    it('should return workspaceId from config', async () => {
      const anchor = new Anchor({ apiKey: 'anc_test_key', workspaceId: 'workspace-123' });
      const workspaceId = await anchor.getWorkspaceId();
      expect(workspaceId).toBe('workspace-123');
    });

    it('should fetch workspaceId from API when not in config', async () => {
      const anchor = new Anchor({ apiKey: 'anc_test_key' });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ workspaces: [{ id: 'workspace-456' }] }),
      } as Response);

      const workspaceId = await anchor.getWorkspaceId();
      expect(workspaceId).toBe('workspace-456');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/workspaces'),
        expect.any(Object)
      );
    });

    it('should return undefined when API call fails', async () => {
      const anchor = new Anchor({ apiKey: 'anc_test_key' });
      // Mock a 401 error response instead of rejection to avoid retry logic
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ error: 'Unauthorized' }),
      } as Response);

      const workspaceId = await anchor.getWorkspaceId();
      expect(workspaceId).toBeUndefined();
    }, 10000);
  });
});

describe('Agents Namespace', () => {
  let anchor: Anchor;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    anchor = new Anchor({
      apiKey: 'anc_test_key',
      baseUrl: 'http://localhost:5050',
    });
    mockFetch.mockClear();
  });

  it('should create an agent', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {
          id: 'agent_123',
          name: 'test-agent',
          status: 'active',
          metadata: {},
          created_at: '2024-01-01T00:00:00Z',
        },
      }),
    } as Response);

    const agent = await anchor.agents.create('test-agent', { env: 'test' });

    expect(agent.id).toBe('agent_123');
    expect(agent.name).toBe('test-agent');
    expect(agent.status).toBe('active');
  });

  it('should create agent with workspaceId override', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {
          id: 'agent_123',
          name: 'test-agent',
          status: 'active',
          metadata: { env: 'test' },
          created_at: '2024-01-01T00:00:00Z',
        },
      }),
    } as Response);

    const agent = await anchor.agents.create('test-agent', { env: 'test' }, 'workspace-override');
    
    const callArgs = mockFetch.mock.calls[0];
    const body = JSON.parse(callArgs[1]?.body as string);
    expect(body.workspaceId).toBe('workspace-override');
    expect(agent.id).toBe('agent_123');
  });

  it('should suspend agent using POST', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: { id: 'agent_123', name: 'test', status: 'suspended' },
      }),
    } as Response);

    const agent = await anchor.agents.suspend('agent_123');

    expect(agent.status).toBe('suspended');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/agents/agent_123/suspend'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('should activate agent using POST', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: { id: 'agent_123', name: 'test', status: 'active' },
      }),
    } as Response);

    const agent = await anchor.agents.activate('agent_123');

    expect(agent.status).toBe('active');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/agents/agent_123/activate'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('should update agent metadata', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent: {
          id: 'agent_123',
          name: 'test-agent',
          status: 'active',
          metadata: { version: '1.1', env: 'production' },
        },
      }),
    } as Response);

    const agent = await anchor.agents.update('agent_123', { version: '1.1' });

    expect(agent.metadata.version).toBe('1.1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/agents/agent_123'),
      expect.objectContaining({ method: 'PATCH' })
    );
  });
});

describe('Config Namespace', () => {
  let anchor: Anchor;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    anchor = new Anchor({
      apiKey: 'anc_test_key',
      baseUrl: 'http://localhost:5050',
    });
    mockFetch.mockClear();
  });

  it('should get config', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent_id: 'agent_123',
        version: 'v1',
        config: {
          behavior: { instructions: 'Be helpful' },
          policies: { block_pii: true },
        },
      }),
    } as Response);

    const config = await anchor.config.get('agent_123');

    expect(config.version).toBe('v1');
    expect(config.config.behavior.instructions).toBe('Be helpful');
  });

  it('should update config', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent_id: 'agent_123',
        version: 'v2',
        config: { behavior: { instructions: 'Updated' } },
      }),
    } as Response);

    const config = await anchor.config.update('agent_123', {
      behavior: { instructions: 'Updated' },
    });

    expect(config.version).toBe('v2');
  });

  it('should rollback config to previous version', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        agent_id: 'agent_123',
        version: 'v3',
        config: { behavior: { instructions: 'Original' } },
        previous_version: 'v2',
      }),
    } as Response);

    const config = await anchor.config.rollback('agent_123', 'v1');

    expect(config.version).toBe('v3');
    expect(config.previousVersion).toBe('v2');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/agents/agent_123/config/rollback'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});

describe('Data Namespace', () => {
  let anchor: Anchor;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    anchor = new Anchor({
      apiKey: 'anc_test_key',
      baseUrl: 'http://localhost:5050',
    });
    mockFetch.mockClear();
  });

  it('should write data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'user:123:pref',
        allowed: true,
        audit_id: 'audit_abc',
      }),
    } as Response);

    const result = await anchor.data.write('agent_123', 'user:123:pref', 'dark_mode');

    expect(result.key).toBe('user:123:pref');
    expect(result.allowed).toBe(true);
  });

  it('should handle blocked write', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        key: 'user:123:ssn',
        allowed: false,
        blocked_by: 'pii_filter',
        reason: 'SSN detected',
        audit_id: 'audit_def',
      }),
    } as Response);

    const result = await anchor.data.write('agent_123', 'user:123:ssn', '123-45-6789');

    expect(result.allowed).toBe(false);
    expect(result.blockedBy).toBe('pii_filter');
  });

  it('should read data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ value: 'dark_mode' }),
    } as Response);

    const value = await anchor.data.read('agent_123', 'user:123:pref');

    expect(value).toBe('dark_mode');
  });

  it('should list keys with prefix', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        keys: [
          { key: 'user:123:language' },
          { key: 'user:123:timezone' },
          { key: 'user:123:preference' },
        ],
      }),
    } as Response);

    const keys = await anchor.data.list('agent_123', { prefix: 'user:123:' });

    expect(keys).toHaveLength(3);
    expect(keys).toContain('user:123:language');
    expect(keys).toContain('user:123:timezone');
    expect(keys).toContain('user:123:preference');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/agents/agent_123/data?'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('should delete data by key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ deleted: true }),
    } as Response);

    const result = await anchor.data.delete('agent_123', 'user:123:temp');

    expect(result).toBe(true);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/agents/agent_123/data/user:123:temp'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});

describe('Checkpoints Namespace', () => {
  let anchor: Anchor;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    anchor = new Anchor({
      apiKey: 'anc_test_key',
      baseUrl: 'http://localhost:5050',
    });
    mockFetch.mockClear();
  });

  it('should create checkpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        id: 'cp_123',
        agent_id: 'agent_123',
        label: 'v1.0',
        config_version: 'v5',
        created_at: '2024-01-01T00:00:00Z',
      }),
    } as Response);

    const checkpoint = await anchor.checkpoints.create('agent_123', { label: 'v1.0' });

    expect(checkpoint.id).toBe('cp_123');
    expect(checkpoint.label).toBe('v1.0');
  });

  it('should restore checkpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        restored_from: 'cp_123',
        config_restored: true,
        config_version: 'v5',
        data_restored: true,
        data_keys_restored: 50,
        data_keys_removed: 10,
        audit_id: 'audit_xyz',
      }),
    } as Response);

    const result = await anchor.checkpoints.restore('agent_123', 'cp_123');

    expect(result.configRestored).toBe(true);
    expect(result.dataKeysRestored).toBe(50);
  });
});

describe('Audit Namespace', () => {
  let anchor: Anchor;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    anchor = new Anchor({
      apiKey: 'anc_test_key',
      baseUrl: 'http://localhost:5050',
    });
    mockFetch.mockClear();
  });

  it('should query audit events', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        events: [
          {
            id: 'audit_1',
            agent_id: 'agent_123',
            operation: 'data.write',
            resource: 'user:123:pref',
            result: 'allowed',
            hash: 'abc123',
            timestamp: '2024-01-01T00:00:00Z',
          },
        ],
      }),
    } as Response);

    const events = await anchor.audit.query('agent_123', { operations: ['data.write'] });

    expect(events).toHaveLength(1);
    expect(events[0].operation).toBe('data.write');
  });

  it('should verify chain', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        valid: true,
        events_checked: 100,
        chain_start: 'audit_001',
        chain_end: 'audit_100',
      }),
    } as Response);

    const verification = await anchor.audit.verify('agent_123');

    expect(verification.valid).toBe(true);
    expect(verification.eventsChecked).toBe(100);
  });

  it('should export audit trail', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        export_id: 'exp_123',
        format: 'json',
        download_url: 'https://example.com/download',
        event_count: 100,
      }),
    } as Response);

    const result = await anchor.audit.export('agent_123', { format: 'json' });

    expect(result.format).toBe('json');
    expect(result.eventCount).toBe(100);
  });
});
