/**
 * HTTP client utilities for Anchor SDK
 */

import { Config, normalizeConfig } from './config';
import {
  AnchorAPIError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ValidationError,
  PolicyViolationError,
  RateLimitError,
  ServerError,
  NetworkError,
} from './exceptions';

// Use native fetch if available
const getFetch = (): typeof fetch => {
  if (typeof fetch !== 'undefined') {
    return fetch;
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require('node-fetch') as typeof fetch;
  } catch {
    throw new Error(
      'fetch is not available. Please use Node.js 18+, install node-fetch, or provide a fetch polyfill.'
    );
  }
};

export class HttpClient {
  private config: Config;
  private warnedAboutWorkspace: boolean = false;

  constructor(config: Config) {
    this.config = config;
  }

  private handleError(statusCode: number, data: Record<string, any>): never {
    const message = data?.message || data?.error || `HTTP ${statusCode}`;

    // Check for policy violation
    if (data?.blocked_by || data?.policy_name) {
      const policyName = data.blocked_by || data.policy_name || 'unknown';
      throw new PolicyViolationError(message, policyName, statusCode, data);
    }

    if (statusCode === 400) {
      throw new ValidationError(message, statusCode, data, data?.field);
    } else if (statusCode === 401) {
      throw new AuthenticationError(message, statusCode, data);
    } else if (statusCode === 403) {
      throw new AuthorizationError(message, statusCode, data, data?.required_permission);
    } else if (statusCode === 404) {
      throw new NotFoundError(message, statusCode, data);
    } else if (statusCode === 429) {
      throw new RateLimitError(message, statusCode, data, data?.retry_after);
    } else if (statusCode >= 500) {
      throw new ServerError(message, statusCode, data);
    } else {
      throw new AnchorAPIError(message, statusCode, data);
    }
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async request<T>(
    method: string,
    endpoint: string,
    data?: Record<string, any>,
    params?: Record<string, any>,
    workspaceId?: string
  ): Promise<T> {
    const baseUrl = this.config.baseUrl || 'https://api.getanchor.dev';
    const timeout = this.config.timeout || 30000;
    const retryAttempts = this.config.retryAttempts ?? 3;
    const retryDelay = this.config.retryDelay || 1000;

    // Use provided workspaceId or fall back to config default
    const effectiveWorkspaceId = workspaceId || this.config.workspaceId;

    // Warn once if workspaceId is not provided
    if (!effectiveWorkspaceId && !this.warnedAboutWorkspace) {
      console.warn(
        'workspaceId is not provided. The API requires workspaceId and will return ' +
        'a ValidationError. To avoid data mixing issues, always provide workspaceId ' +
        'when initializing Anchor() or pass it per-operation.'
      );
      this.warnedAboutWorkspace = true;
    }

    // Add workspaceId to request body for POST/PUT/PATCH requests
    let requestData = data;
    if (effectiveWorkspaceId && data !== undefined) {
      requestData = { ...data };
      if (!requestData.workspaceId) {
        requestData.workspaceId = effectiveWorkspaceId;
      }
    }

    // Add workspaceId to query params for GET/DELETE requests
    let requestParams = params;
    if (effectiveWorkspaceId && (method === 'GET' || method === 'DELETE')) {
      requestParams = { ...(params || {}) };
      if (!requestParams.workspaceId) {
        requestParams.workspaceId = effectiveWorkspaceId;
      }
    }

    const url = new URL(`${baseUrl}${endpoint}`);

    if (requestParams) {
      Object.entries(requestParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const headers: Record<string, string> = {
      'User-Agent': 'anchorai-typescript/1.0.1',
    };

    if (this.config.apiKey) {
      headers['X-API-Key'] = this.config.apiKey;
    }

    if (data !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const fetchFn = getFetch();
        let response: Response;

        try {
          response = await fetchFn(url.toString(), {
            method,
            headers,
            body: requestData ? JSON.stringify(requestData) : undefined,
            signal: controller.signal,
          });
        } catch (fetchError: any) {
          clearTimeout(timeoutId);
          if (fetchError?.name === 'AbortError') {
            lastError = new NetworkError(`Request timeout after ${timeout}ms`);
          } else {
            lastError = new NetworkError(`Request failed: ${fetchError?.message || String(fetchError)}`);
          }
          if (attempt < retryAttempts) {
            await this.sleep(retryDelay * Math.pow(2, attempt));
            continue;
          }
          throw lastError;
        }

        clearTimeout(timeoutId);

        let responseData: any;
        try {
          const text = await response.text();
          if (text) {
            try {
              responseData = JSON.parse(text);
            } catch {
              responseData = { error: text };
            }
          } else {
            responseData = {};
          }
        } catch {
          responseData = {};
        }

        if (response.ok) {
          return responseData as T;
        }

        const statusCode = response.status || 500;

        // Don't retry on client errors (4xx), except 429
        if (statusCode >= 400 && statusCode < 500 && statusCode !== 429) {
          this.handleError(statusCode, responseData);
        }

        // Retry on server errors (5xx) and rate limits (429)
        if (attempt < retryAttempts) {
          await this.sleep(retryDelay * Math.pow(2, attempt));
          continue;
        } else {
          this.handleError(statusCode, responseData);
        }
      } catch (error: any) {
        // Re-throw API errors immediately
        if (error instanceof AnchorAPIError) {
          throw error;
        }

        if (error?.name === 'AbortError') {
          lastError = new NetworkError(`Request timeout after ${timeout}ms`);
        } else if (!(error instanceof NetworkError)) {
          lastError = new NetworkError(`Request failed: ${error?.message || String(error)}`);
        } else {
          lastError = error;
        }

        if (attempt < retryAttempts) {
          await this.sleep(retryDelay * Math.pow(2, attempt));
          continue;
        }
      }
    }

    if (lastError) {
      throw lastError;
    }
    throw new NetworkError('Request failed after retries');
  }

  async get<T>(endpoint: string, params?: Record<string, any>, workspaceId?: string): Promise<T> {
    return this.request<T>('GET', endpoint, undefined, params, workspaceId);
  }

  async post<T>(endpoint: string, data?: Record<string, any>, params?: Record<string, any>, workspaceId?: string): Promise<T> {
    return this.request<T>('POST', endpoint, data, params, workspaceId);
  }

  async put<T>(endpoint: string, data?: Record<string, any>, params?: Record<string, any>, workspaceId?: string): Promise<T> {
    return this.request<T>('PUT', endpoint, data, params, workspaceId);
  }

  async patch<T>(endpoint: string, data?: Record<string, any>, params?: Record<string, any>, workspaceId?: string): Promise<T> {
    return this.request<T>('PATCH', endpoint, data, params, workspaceId);
  }

  async delete<T>(endpoint: string, params?: Record<string, any>, workspaceId?: string): Promise<T> {
    return this.request<T>('DELETE', endpoint, undefined, params, workspaceId);
  }
}
