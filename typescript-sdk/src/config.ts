/**
 * Configuration for Anchor SDK
 */

export interface Config {
  apiKey: string;
  workspaceId?: string;
  baseUrl?: string;
  region?: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  batchSize?: number;
  cachePolicies?: boolean;
  verifySsl?: boolean;
  logLevel?: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
}

/**
 * Anchor configuration options (alias for Config)
 */
export type AnchorConfig = Partial<Config>;

export const DEFAULT_CONFIG: Partial<Config> = {
  baseUrl: 'https://api.getanchor.dev',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  batchSize: 100,
  cachePolicies: true,
  verifySsl: true,
  logLevel: 'INFO',
};

export function normalizeConfig(config: AnchorConfig): Config {
  // Get API key from config or environment
  const apiKey = config.apiKey || process.env.ANCHOR_API_KEY || '';

  const normalized: Config = {
    apiKey,
    workspaceId: config.workspaceId,
    baseUrl: config.baseUrl || DEFAULT_CONFIG.baseUrl || 'https://api.getanchor.dev',
    region: config.region || DEFAULT_CONFIG.region,
    timeout: config.timeout ?? DEFAULT_CONFIG.timeout,
    retryAttempts: config.retryAttempts ?? DEFAULT_CONFIG.retryAttempts,
    retryDelay: config.retryDelay ?? DEFAULT_CONFIG.retryDelay,
    batchSize: config.batchSize ?? DEFAULT_CONFIG.batchSize,
    cachePolicies: config.cachePolicies ?? DEFAULT_CONFIG.cachePolicies,
    verifySsl: config.verifySsl ?? DEFAULT_CONFIG.verifySsl,
    logLevel: config.logLevel || DEFAULT_CONFIG.logLevel,
  };

  // Normalize base URL
  if (normalized.baseUrl) {
    normalized.baseUrl = normalized.baseUrl.replace(/\/$/, '');
  }

  // Handle regional endpoints
  if (normalized.region && normalized.baseUrl?.includes('api.getanchor.dev')) {
    normalized.baseUrl = `https://${normalized.region}.api.getanchor.dev`;
  }

  return normalized;
}
