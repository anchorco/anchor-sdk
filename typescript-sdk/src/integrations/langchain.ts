/**
 * LangChain integration for Anchor SDK
 *
 * Provides policy-enforced memory and chat history for LangChain.
 *
 * @example
 * ```typescript
 * import { Anchor } from 'anchorai';
 * import { AnchorMemory } from 'anchorai/integrations';
 *
 * const anchor = new Anchor({ apiKey: 'your-api-key' });
 * const memory = new AnchorMemory(anchor, agentId);
 *
 * // Use with LangChain chains/agents
 * await memory.saveContext({ input: 'Hello' }, { output: 'Hi there!' });
 * const history = await memory.loadMemoryVariables({});
 * ```
 */

import type { Anchor } from '../anchor';

// Generate a cryptographically secure random string suitable for session IDs.
function getSecureRandomString(length: number): string {
  const alphabet =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

  // Browser / WebCrypto
  const globalCrypto: Crypto | undefined =
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (typeof globalThis !== 'undefined' && (globalThis as any).crypto) ||
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (typeof window !== 'undefined' && (window as any).crypto);

  if (globalCrypto && typeof globalCrypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(length);
    globalCrypto.getRandomValues(bytes);
    let result = '';
    for (let i = 0; i < length; i++) {
      result += alphabet[bytes[i] % alphabet.length];
    }
    return result;
  }

  // Node.js crypto
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const nodeCrypto = require('crypto');
    const bytes: Buffer = nodeCrypto.randomBytes(length);
    let result = '';
    for (let i = 0; i < length; i++) {
      result += alphabet[bytes[i] % alphabet.length];
    }
    return result;
  } catch {
    // Fallback: not cryptographically secure, but avoids runtime failure
    let result = '';
    for (let i = 0; i < length; i++) {
      const idx = Math.floor(Math.random() * alphabet.length);
      result += alphabet[idx];
    }
    return result;
  }
}

/**
 * Message structure for chat history
 */
export interface ChatMessage {
  role: 'human' | 'ai' | 'system';
  content: string;
  metadata?: Record<string, any>;
}

/**
 * LangChain-compatible memory backed by Anchor.
 *
 * Features:
 * - Policy-checked writes (blocks PII, secrets, etc.)
 * - Persistent storage across sessions
 * - Checkpoint/rollback support
 * - Full audit trail
 */
export class AnchorMemory {
  private anchor: Anchor;
  private agentId: string;
  private memoryKey: string;
  private returnMessages: boolean;
  private sessionId: string;
  private messages: ChatMessage[] = [];

  constructor(
    anchor: Anchor,
    agentId: string,
    options?: {
      memoryKey?: string;
      returnMessages?: boolean;
      sessionId?: string;
    }
  ) {
    this.anchor = anchor;
    this.agentId = agentId;
    this.memoryKey = options?.memoryKey || 'chat_history';
    this.returnMessages = options?.returnMessages ?? true;
    this.sessionId = options?.sessionId || this.generateSessionId();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Get the memory variables (keys returned by this memory)
   */
  get memoryVariables(): string[] {
    return [this.memoryKey];
  }

  /**
   * Save conversation context to Anchor.
   */
  async saveContext(
    inputs: Record<string, any>,
    outputs: Record<string, any>
  ): Promise<void> {
    const inputKey = Object.keys(inputs)[0] || 'input';
    const outputKey = Object.keys(outputs)[0] || 'output';

    const humanMessage = inputs[inputKey];
    const aiMessage = outputs[outputKey];

    if (humanMessage) {
      const timestamp = Date.now();
      await this.anchor.data.write(
        this.agentId,
        `chat:${this.sessionId}:human:${timestamp}`,
        String(humanMessage),
        { role: 'human', session_id: this.sessionId }
      );
      this.messages.push({ role: 'human', content: String(humanMessage) });
    }

    if (aiMessage) {
      const timestamp = Date.now();
      await this.anchor.data.write(
        this.agentId,
        `chat:${this.sessionId}:ai:${timestamp}`,
        String(aiMessage),
        { role: 'ai', session_id: this.sessionId }
      );
      this.messages.push({ role: 'ai', content: String(aiMessage) });
    }
  }

  /**
   * Load memory variables from Anchor.
   */
  async loadMemoryVariables(
    _inputs: Record<string, any>
  ): Promise<Record<string, any>> {
    await this.loadFromAnchor();

    if (this.returnMessages) {
      return { [this.memoryKey]: this.messages };
    }

    // Return as formatted string
    const formatted = this.messages
      .map((m) => `${m.role === 'human' ? 'Human' : 'AI'}: ${m.content}`)
      .join('\n');
    return { [this.memoryKey]: formatted };
  }

  private async loadFromAnchor(): Promise<void> {
    const keys = await this.anchor.data.list(this.agentId, {
      prefix: `chat:${this.sessionId}:`,
    });

    this.messages = [];
    for (const key of keys.sort()) {
      const entry = await this.anchor.data.readFull(this.agentId, key);
      if (entry) {
        const role = key.includes(':human:') ? 'human' : 'ai';
        this.messages.push({
          role,
          content: entry.value,
          metadata: entry.metadata,
        });
      }
    }
  }

  /**
   * Clear memory.
   */
  async clear(): Promise<void> {
    this.messages = [];
    await this.anchor.data.deletePrefix(this.agentId, `chat:${this.sessionId}:`);
  }

  /**
   * Create a checkpoint of current memory state.
   */
  async createCheckpoint(label?: string): Promise<string> {
    const checkpoint = await this.anchor.checkpoints.create(this.agentId, {
      label: label || `memory-checkpoint-${Date.now()}`,
    });
    return checkpoint.id;
  }

  /**
   * Restore memory to a checkpoint.
   */
  async restoreCheckpoint(checkpointId: string): Promise<void> {
    await this.anchor.checkpoints.restore(this.agentId, checkpointId);
    this.messages = [];
    await this.loadFromAnchor();
  }
}

/**
 * LangChain-compatible chat message history backed by Anchor.
 *
 * Drop-in replacement for BaseChatMessageHistory.
 */
export class AnchorChatHistory {
  private anchor: Anchor;
  private agentId: string;
  private sessionId: string;
  private cachedMessages: ChatMessage[] = [];

  constructor(
    anchor: Anchor,
    agentId: string,
    options?: { sessionId?: string }
  ) {
    this.anchor = anchor;
    this.agentId = agentId;
    this.sessionId =
      options?.sessionId ||
      `session_${Date.now()}_${getSecureRandomString(16)}`;
  }

  /**
   * Get all messages in the history.
   */
  async getMessages(): Promise<ChatMessage[]> {
    const keys = await this.anchor.data.list(this.agentId, {
      prefix: `chat:${this.sessionId}:`,
    });

    this.cachedMessages = [];
    for (const key of keys.sort()) {
      const entry = await this.anchor.data.readFull(this.agentId, key);
      if (entry) {
        const role = key.includes(':human:')
          ? 'human'
          : key.includes(':system:')
          ? 'system'
          : 'ai';
        this.cachedMessages.push({
          role,
          content: entry.value,
          metadata: entry.metadata,
        });
      }
    }
    return this.cachedMessages;
  }

  /**
   * Add a message to the history.
   */
  async addMessage(message: ChatMessage): Promise<void> {
    const timestamp = Date.now();
    await this.anchor.data.write(
      this.agentId,
      `chat:${this.sessionId}:${message.role}:${timestamp}`,
      message.content,
      { role: message.role, session_id: this.sessionId, ...message.metadata }
    );
    this.cachedMessages.push(message);
  }

  /**
   * Add a human message.
   */
  async addUserMessage(content: string): Promise<void> {
    await this.addMessage({ role: 'human', content });
  }

  /**
   * Add an AI message.
   */
  async addAIMessage(content: string): Promise<void> {
    await this.addMessage({ role: 'ai', content });
  }

  /**
   * Clear all messages.
   */
  async clear(): Promise<void> {
    this.cachedMessages = [];
    await this.anchor.data.deletePrefix(this.agentId, `chat:${this.sessionId}:`);
  }
}
