/**
 * Tests for HTTP client utilities.
 */

/// <reference types="jest" />

import { HttpClient } from '../http';
import { Config } from '../config';
import {
  AnchorAPIError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  NetworkError,
  PolicyViolationError,
} from '../exceptions';

// Mock fetch globally
global.fetch = jest.fn();

// Disable telemetry in tests
process.env.ANCHOR_TELEMETRY = '0';

describe('HttpClient', () => {
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
  let config: Config;
  let httpClient: HttpClient;

  beforeEach(() => {
    mockFetch.mockClear();
    config = {
      apiKey: 'anc_test_key',
      baseUrl: 'https://api.getanchor.dev',
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 100, // Short delay for tests
    };
    httpClient = new HttpClient(config);
  });

  describe('Initialization', () => {
    it('should initialize with config', () => {
      expect(httpClient).toBeDefined();
    });
  });

  describe('Successful Requests', () => {
    it('should make a successful GET request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ result: 'success' }),
      } as Response);

      const result = await httpClient.get<{ result: string }>('/v1/test');

      expect(result).toEqual({ result: 'success' });
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.getanchor.dev/v1/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'X-API-Key': 'anc_test_key',
            'User-Agent': 'anchorai-typescript/1.0.1',
          }),
        })
      );
    });

    it('should handle empty response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => '',
      } as Response);

      const result = await httpClient.get<Record<string, any>>('/v1/test');

      expect(result).toEqual({});
    });

    it('should make POST request with JSON data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ id: '123' }),
      } as Response);

      const result = await httpClient.post<{ id: string }>('/v1/test', { name: 'test' });

      expect(result).toEqual({ id: '123' });
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.getanchor.dev/v1/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'test' }),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should make PUT request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ updated: true }),
      } as Response);

      const result = await httpClient.put<{ updated: boolean }>('/v1/test', { name: 'updated' });

      expect(result).toEqual({ updated: true });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'PUT' })
      );
    });

    it('should make PATCH request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ patched: true }),
      } as Response);

      const result = await httpClient.patch<{ patched: boolean }>('/v1/test', { name: 'patched' });

      expect(result).toEqual({ patched: true });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'PATCH' })
      );
    });

    it('should make DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ deleted: true }),
      } as Response);

      const result = await httpClient.delete<{ deleted: boolean }>('/v1/test');

      expect(result).toEqual({ deleted: true });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: 'DELETE' })
      );
    });

    it('should include query parameters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ items: [] }),
      } as Response);

      await httpClient.get('/v1/test', { limit: 10, offset: 0 });

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.getanchor.dev/v1/test?limit=10&offset=0',
        expect.any(Object)
      );
    });

    it('should skip undefined/null params', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ items: [] }),
      } as Response);

      await httpClient.get('/v1/test', { limit: 10, offset: undefined, filter: null });

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.getanchor.dev/v1/test?limit=10',
        expect.any(Object)
      );
    });
  });

  describe('Error Handling', () => {
    it('should throw ValidationError on 400', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => JSON.stringify({ message: 'Invalid input', field: 'name' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(ValidationError);

      try {
        await httpClient.get('/v1/test');
      } catch (error) {
        // Reset mock for the second call
      }
    });

    it('should include field in ValidationError', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => JSON.stringify({ message: 'Invalid input', field: 'email' }),
      } as Response);

      try {
        await httpClient.get('/v1/test');
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
        expect((error as ValidationError).field).toBe('email');
      }
    });

    it('should throw AuthenticationError on 401', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ message: 'Invalid API key' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(AuthenticationError);
    });

    it('should throw AuthorizationError on 403', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        text: async () => JSON.stringify({ message: 'Permission denied', required_permission: 'write:data' }),
      } as Response);

      try {
        await httpClient.get('/v1/test');
      } catch (error) {
        expect(error).toBeInstanceOf(AuthorizationError);
        expect((error as AuthorizationError).requiredPermission).toBe('write:data');
      }
    });

    it('should throw NotFoundError on 404', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ message: 'Resource not found' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(NotFoundError);
    });

    it('should throw RateLimitError on 429', async () => {
      // First call fails with 429, second succeeds after retry
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          text: async () => JSON.stringify({ message: 'Rate limit exceeded', retry_after: 60 }),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          text: async () => JSON.stringify({ result: 'success' }),
        } as Response);

      const result = await httpClient.get('/v1/test');
      expect(result).toEqual({ result: 'success' });
    });

    it('should include retry_after in RateLimitError after max retries', async () => {
      // All calls fail with 429
      mockFetch.mockResolvedValue({
        ok: false,
        status: 429,
        text: async () => JSON.stringify({ message: 'Rate limit exceeded', retry_after: 60 }),
      } as Response);

      try {
        await httpClient.get('/v1/test');
      } catch (error) {
        expect(error).toBeInstanceOf(RateLimitError);
        expect((error as RateLimitError).retryAfter).toBe(60);
      }
    });

    it('should throw ServerError on 500', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ message: 'Internal server error' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(ServerError);
    });

    it('should throw ServerError on 502', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 502,
        text: async () => JSON.stringify({ message: 'Bad gateway' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(ServerError);
    });

    it('should throw ServerError on 503', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 503,
        text: async () => JSON.stringify({ message: 'Service unavailable' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(ServerError);
    });

    it('should throw PolicyViolationError when blocked_by is present', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => JSON.stringify({ message: 'Blocked by policy', blocked_by: 'pii_filter' }),
      } as Response);

      try {
        await httpClient.get('/v1/test');
      } catch (error) {
        expect(error).toBeInstanceOf(PolicyViolationError);
        expect((error as PolicyViolationError).policyName).toBe('pii_filter');
      }
    });

    it('should handle invalid JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Server error text',
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(ServerError);
    });
  });

  describe('Retry Logic', () => {
    it('should retry on server error and succeed', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          text: async () => JSON.stringify({ message: 'Server error' }),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          text: async () => JSON.stringify({ result: 'success' }),
        } as Response);

      const result = await httpClient.get('/v1/test');

      expect(result).toEqual({ result: 'success' });
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('should retry on network error and succeed', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Connection failed'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          text: async () => JSON.stringify({ result: 'success' }),
        } as Response);

      const result = await httpClient.get('/v1/test');

      expect(result).toEqual({ result: 'success' });
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('should NOT retry on 4xx errors (except 429)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => JSON.stringify({ message: 'Bad request' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(ValidationError);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should NOT retry on 401 errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ message: 'Unauthorized' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(AuthenticationError);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should NOT retry on 403 errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        text: async () => JSON.stringify({ message: 'Forbidden' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(AuthorizationError);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should NOT retry on 404 errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ message: 'Not found' }),
      } as Response);

      await expect(httpClient.get('/v1/test')).rejects.toThrow(NotFoundError);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should retry on 429 rate limit errors', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          text: async () => JSON.stringify({ message: 'Rate limited' }),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          text: async () => JSON.stringify({ result: 'success' }),
        } as Response);

      const result = await httpClient.get('/v1/test');

      expect(result).toEqual({ result: 'success' });
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('should throw NetworkError after max retries on network failure', async () => {
      mockFetch.mockRejectedValue(new Error('Connection failed'));

      await expect(httpClient.get('/v1/test')).rejects.toThrow(NetworkError);
      // Initial attempt + 3 retries = 4 total
      expect(mockFetch).toHaveBeenCalledTimes(4);
    });

    it('should use exponential backoff', async () => {
      const sleepSpy = jest.spyOn(global, 'setTimeout');

      mockFetch
        .mockRejectedValueOnce(new Error('Connection failed'))
        .mockRejectedValueOnce(new Error('Connection failed'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          text: async () => JSON.stringify({ result: 'success' }),
        } as Response);

      await httpClient.get('/v1/test');

      // Check that setTimeout was called with increasing delays
      // First retry: 100ms * 2^0 = 100ms
      // Second retry: 100ms * 2^1 = 200ms
      const timeoutCalls = sleepSpy.mock.calls.filter(
        (call) => typeof call[1] === 'number' && call[1] >= 100
      );
      expect(timeoutCalls.length).toBeGreaterThanOrEqual(2);

      sleepSpy.mockRestore();
    });
  });

  describe('Timeout Handling', () => {
    it('should throw NetworkError on timeout', async () => {
      // Create client with very short timeout
      const shortTimeoutConfig: Config = {
        apiKey: 'anc_test_key',
        baseUrl: 'https://api.getanchor.dev',
        timeout: 1, // 1ms timeout
        retryAttempts: 0, // No retries for this test
      };
      const shortTimeoutClient = new HttpClient(shortTimeoutConfig);

      // Mock fetch to hang
      mockFetch.mockImplementation(() => new Promise(() => {}));

      // Use AbortError to simulate timeout
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';
      mockFetch.mockRejectedValue(abortError);

      await expect(shortTimeoutClient.get('/v1/test')).rejects.toThrow(NetworkError);
    });
  });

  describe('Headers', () => {
    it('should include API key header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({}),
      } as Response);

      await httpClient.get('/v1/test');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-API-Key': 'anc_test_key',
          }),
        })
      );
    });

    it('should include User-Agent header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({}),
      } as Response);

      await httpClient.get('/v1/test');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'User-Agent': 'anchorai-typescript/1.0.1',
          }),
        })
      );
    });

    it('should include Content-Type for POST requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({}),
      } as Response);

      await httpClient.post('/v1/test', { data: 'test' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should not include Content-Type for GET requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({}),
      } as Response);

      await httpClient.get('/v1/test');

      const callArgs = mockFetch.mock.calls[0];
      const headers = callArgs[1]?.headers as Record<string, string>;
      expect(headers['Content-Type']).toBeUndefined();
    });
  });

  describe('Response Parsing', () => {
    it('should parse JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ key: 'value', nested: { a: 1 } }),
      } as Response);

      const result = await httpClient.get<{ key: string; nested: { a: number } }>('/v1/test');

      expect(result).toEqual({ key: 'value', nested: { a: 1 } });
    });

    it('should handle non-JSON response as error text', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => 'plain text response',
      } as Response);

      const result = await httpClient.get('/v1/test');

      expect(result).toEqual({ error: 'plain text response' });
    });
  });

  describe('WorkspaceId Support', () => {
    let httpClientWithWorkspace: HttpClient;
    let httpClientWithoutWorkspace: HttpClient;

    beforeEach(() => {
      const configWithWorkspace: Config = {
        apiKey: 'anc_test_key',
        workspaceId: 'workspace-123',
        baseUrl: 'https://api.getanchor.dev',
      };
      httpClientWithWorkspace = new HttpClient(configWithWorkspace);

      const configWithoutWorkspace: Config = {
        apiKey: 'anc_test_key',
        baseUrl: 'https://api.getanchor.dev',
      };
      httpClientWithoutWorkspace = new HttpClient(configWithoutWorkspace);
    });

    it('should include workspaceId in POST request body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ success: true }),
      } as Response);

      await httpClientWithWorkspace.post('/agents', { name: 'test-agent' });

      const callArgs = mockFetch.mock.calls[0];
      const body = JSON.parse(callArgs[1]?.body as string);
      expect(body.workspaceId).toBe('workspace-123');
      expect(body.name).toBe('test-agent');
    });

    it('should include workspaceId in GET request params', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ agents: [] }),
      } as Response);

      await httpClientWithWorkspace.get('/agents');

      const callArgs = mockFetch.mock.calls[0];
      const url = new URL(callArgs[0] as string);
      expect(url.searchParams.get('workspaceId')).toBe('workspace-123');
    });

    it('should include workspaceId in PUT request body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ updated: true }),
      } as Response);

      await httpClientWithWorkspace.put('/agents/123', { name: 'updated' });

      const callArgs = mockFetch.mock.calls[0];
      const body = JSON.parse(callArgs[1]?.body as string);
      expect(body.workspaceId).toBe('workspace-123');
    });

    it('should include workspaceId in DELETE request params', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ deleted: true }),
      } as Response);

      await httpClientWithWorkspace.delete('/agents/123');

      const callArgs = mockFetch.mock.calls[0];
      const url = new URL(callArgs[0] as string);
      expect(url.searchParams.get('workspaceId')).toBe('workspace-123');
    });

    it('should allow per-request workspaceId override', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ success: true }),
      } as Response);

      await httpClientWithWorkspace.post('/agents', { name: 'test' }, undefined, 'workspace-override');

      const callArgs = mockFetch.mock.calls[0];
      const body = JSON.parse(callArgs[1]?.body as string);
      expect(body.workspaceId).toBe('workspace-override');
    });

    it('should not override existing workspaceId in data', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ success: true }),
      } as Response);

      await httpClientWithWorkspace.post('/agents', { name: 'test', workspaceId: 'workspace-999' });

      const callArgs = mockFetch.mock.calls[0];
      const body = JSON.parse(callArgs[1]?.body as string);
      expect(body.workspaceId).toBe('workspace-999');
    });

    it('should warn when workspaceId is not provided', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ success: true }),
      } as Response);

      await httpClientWithoutWorkspace.post('/agents', { name: 'test' });

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('workspaceId is not provided')
      );
      consoleSpy.mockRestore();
    });
  });
});
