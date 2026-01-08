/**
 * Agents namespace: Agent registry and lifecycle management.
 * @module
 */

import { HttpClient } from '../http';
import { NotFoundError } from '../exceptions';

/**
 * Agent record.
 */
export interface Agent {
  /** Agent ID */
  id: string;
  /** Human-readable name */
  name: string;
  /** Status: "active" or "suspended" */
  status: 'active' | 'suspended';
  /** Custom metadata */
  metadata: Record<string, any>;
  /** Current config version */
  configVersion?: string;
  /** Number of data entries */
  dataCount?: number;
  /** Number of checkpoints */
  checkpointCount?: number;
  /** When the agent was created */
  createdAt?: Date;
  /** When the agent was last updated */
  updatedAt?: Date;
}

function parseAgent(data: Record<string, any>): Agent {
  return {
    id: data.id || data.agent_id || '',
    name: data.name || '',
    status: data.status || 'active',
    metadata: data.metadata || data.config || {},
    configVersion: data.config_version,
    dataCount: data.data_count,
    checkpointCount: data.checkpoint_count,
    createdAt: data.created_at ? new Date(data.created_at) : undefined,
    updatedAt: data.updated_at ? new Date(data.updated_at) : undefined,
  };
}

/**
 * Agent management operations.
 *
 * @example
 * ```typescript
 * const anchor = new Anchor({ apiKey: 'your-api-key' });
 *
 * // Create agent
 * const agent = await anchor.agents.create('support-bot', {
 *   environment: 'production',
 *   version: '1.0.0'
 * });
 *
 * // Lifecycle operations
 * const agents = await anchor.agents.list({ status: 'active' });
 * await anchor.agents.suspend(agent.id);
 * await anchor.agents.activate(agent.id);
 * await anchor.agents.delete(agent.id);
 * ```
 */
export class AgentsNamespace {
  constructor(private http: HttpClient) {}

  /**
   * Create a new agent.
   *
   * @param name - Human-readable agent name
   * @param metadata - Optional key-value metadata
   * @param workspaceId - Optional workspace ID (overrides client default)
   * @returns Created Agent object
   */
  async create(name: string, metadata?: Record<string, any>, workspaceId?: string): Promise<Agent> {
    const response = await this.http.post<{ agent: Record<string, any> }>('/agents', {
      name,
      metadata: metadata || {},
    }, undefined, workspaceId);
    return parseAgent(response.agent || response);
  }

  /**
   * Get an agent by ID.
   *
   * @param agentId - Agent ID (e.g., "agent_a1b2c3")
   * @returns Agent object, or null if not found
   */
  async get(agentId: string): Promise<Agent | null> {
    try {
      const response = await this.http.get<{ agent: Record<string, any> }>(`/agents/${agentId}`);
      return parseAgent(response.agent || response);
    } catch (error) {
      if (error instanceof NotFoundError) return null;
      throw error;
    }
  }

  /**
   * List agents.
   *
   * @param options - Filter options
   * @param options.status - Filter by status ("active" or "suspended")
   * @param options.limit - Max results (default: 50)
   * @param options.offset - Pagination offset
   * @returns List of Agent objects
   */
  async list(options?: { status?: 'active' | 'suspended'; limit?: number; offset?: number }): Promise<Agent[]> {
    const params: Record<string, any> = {
      limit: Math.min(options?.limit || 50, 100),
      offset: options?.offset || 0,
    };
    if (options?.status) params.status = options.status;

    const response = await this.http.get<{ agents: Record<string, any>[] }>('/agents', params);
    return (response.agents || []).map(parseAgent);
  }

  /**
   * Update agent metadata.
   *
   * @param agentId - Agent ID
   * @param metadata - New metadata (merged with existing)
   * @returns Updated Agent object
   */
  async update(agentId: string, metadata: Record<string, any>): Promise<Agent> {
    const response = await this.http.patch<{ agent: Record<string, any> }>(`/agents/${agentId}`, {
      metadata,
    });
    return parseAgent(response.agent || response);
  }

  /**
   * Delete an agent.
   *
   * @param agentId - Agent ID
   * @returns True if deleted
   */
  async delete(agentId: string): Promise<boolean> {
    await this.http.delete(`/agents/${agentId}`);
    return true;
  }

  /**
   * Suspend an agent. Suspended agents cannot perform operations.
   *
   * @param agentId - Agent ID
   * @returns Updated Agent object
   */
  async suspend(agentId: string): Promise<Agent> {
    const response = await this.http.post<{ agent: Record<string, any> }>(`/agents/${agentId}/suspend`);
    return parseAgent(response.agent || response);
  }

  /**
   * Activate a suspended agent.
   *
   * @param agentId - Agent ID
   * @returns Updated Agent object
   */
  async activate(agentId: string): Promise<Agent> {
    const response = await this.http.post<{ agent: Record<string, any> }>(`/agents/${agentId}/activate`);
    return parseAgent(response.agent || response);
  }
}
