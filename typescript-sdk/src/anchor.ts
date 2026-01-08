/**
 * Anchor: Control what your AI agents store. Audit everything.
 *
 * Anchor lets you persist agent state, block bad data, prove what happened.
 *
 * @example Quick Start
 * ```typescript
 * import { Anchor } from 'anchorai';
 *
 * const anchor = new Anchor({ apiKey: 'your-api-key' });
 * const agent = await anchor.agents.create('my-agent');
 * ```
 *
 * @example Full Example
 * ```typescript
 * import { Anchor } from 'anchorai';
 *
 * const anchor = new Anchor({ apiKey: 'your-api-key' });
 *
 * // Create agent
 * const agent = await anchor.agents.create('support-bot', {
 *   environment: 'production'
 * });
 *
 * // Store data (automatically audit-logged)
 * const result = await anchor.data.write(agent.id, 'user:123:pref', 'concise answers');
 * console.log(result.allowed); // true
 *
 * // PII gets blocked by policy
 * const blocked = await anchor.data.write(agent.id, 'user:123:ssn', '123-45-6789');
 * console.log(blocked.allowed); // false - blocked by policy
 *
 * // Checkpoint before risky operation
 * const checkpoint = await anchor.checkpoints.create(agent.id, { label: 'pre-update' });
 *
 * // Something goes wrong? Rollback
 * await anchor.checkpoints.restore(agent.id, checkpoint.id);
 *
 * // Prove what happened
 * const events = await anchor.audit.query(agent.id, { limit: 5 });
 * ```
 */

import { Config, normalizeConfig, AnchorConfig } from './config';
import { HttpClient } from './http';
import { AgentsNamespace } from './namespaces/agents';
import { ConfigNamespace } from './namespaces/config';
import { DataNamespace } from './namespaces/data';
import { CheckpointsNamespace } from './namespaces/checkpoints';
import { AuditNamespace } from './namespaces/audit';

/**
 * Anchor client for AI agent state management.
 *
 * @example Simple initialization
 * ```typescript
 * const anchor = new Anchor({ apiKey: 'your-api-key' });
 * ```
 *
 * @example With configuration
 * ```typescript
 * const anchor = new Anchor({
 *   apiKey: 'your-api-key',
 *   baseUrl: 'https://api.getanchor.dev',
 *   timeout: 30000,
 *   retryAttempts: 3
 * });
 * ```
 *
 * Namespaces:
 * - `anchor.agents` - Agent registry and lifecycle
 * - `anchor.config` - Agent configuration with versioning
 * - `anchor.data` - Governed key-value data storage
 * - `anchor.checkpoints` - State snapshots and rollback
 * - `anchor.audit` - Hash-chained audit trail
 */
export class Anchor {
  private readonly _config: Config;
  private readonly _http: HttpClient;

  // Namespaces (5 per spec)
  private readonly _agents: AgentsNamespace;
  private readonly _configNs: ConfigNamespace;
  private readonly _data: DataNamespace;
  private readonly _checkpoints: CheckpointsNamespace;
  private readonly _audit: AuditNamespace;

  /**
   * Initialize Anchor client.
   *
   * @param options - Configuration options
   * @param options.apiKey - API key (or set ANCHOR_API_KEY env var)
   * @param options.workspaceId - Workspace ID (optional, can also be passed per-operation)
   * @param options.baseUrl - API base URL (default: https://api.getanchor.dev)
   * @param options.timeout - Request timeout in ms (default: 30000)
   * @param options.retryAttempts - Number of retry attempts (default: 3)
   */
  constructor(options?: AnchorConfig) {
    this._config = normalizeConfig(options || {});
    this._http = new HttpClient(this._config);

    // Initialize namespaces (5 per spec)
    this._agents = new AgentsNamespace(this._http);
    this._configNs = new ConfigNamespace(this._http);
    this._data = new DataNamespace(this._http);
    this._checkpoints = new CheckpointsNamespace(this._http);
    this._audit = new AuditNamespace(this._http);
  }

  /**
   * Agent registry and lifecycle management.
   */
  get agents(): AgentsNamespace {
    return this._agents;
  }

  /**
   * Agent configuration with versioning.
   */
  get config(): ConfigNamespace {
    return this._configNs;
  }

  /**
   * Governed key-value data storage.
   */
  get data(): DataNamespace {
    return this._data;
  }

  /**
   * State snapshots and rollback.
   */
  get checkpoints(): CheckpointsNamespace {
    return this._checkpoints;
  }

  /**
   * Hash-chained audit trail.
   */
  get audit(): AuditNamespace {
    return this._audit;
  }

  /**
   * Get the current client configuration.
   */
  get clientConfig(): Config {
    return this._config;
  }

  /**
   * Attempt to fetch the default workspace ID for the current API key.
   *
   * This is a convenience method. If it fails, you should provide workspaceId
   * explicitly when initializing Anchor() or get it from the signup flow.
   *
   * @returns Workspace ID if found, undefined otherwise
   *
   */
  async getWorkspaceId(): Promise<string | undefined> {
    if (this._config.workspaceId) {
      return this._config.workspaceId;
    }

    try {
      const response = await this._http.get<{ workspaces?: Array<{ id?: string; workspaceId?: string }> }>('/workspaces');
      const workspaces = response.workspaces || (Array.isArray(response) ? response : []);
      if (workspaces.length > 0) {
        return workspaces[0].id || workspaces[0].workspaceId;
      }
    } catch (error) {
      // If endpoint doesn't exist or fails, return undefined
      console.warn('Could not fetch workspace ID:', error);
    }

    return undefined;
  }
}
