/**
 * Default policy configurations for Anchor agents.
 */
export interface DefaultPolicyPackConfig {
    allowedDomains?: string[] | null;
    maxQuerySize?: number | null;
    requireApprovalFor?: string[] | null;
    blockPii?: boolean;
    blockSecrets?: boolean;
}

const DEFAULT_POLICY_CONFIG = {
    maxQuerySize: 1000,
    requireApprovalFor: ['delete', 'update', 'export'],
    blockPii: true,
    blockSecrets: true,
} as const;

/**
 * Production ready default policies for agent config.
 *
 * @example
 * ```typescript
 * import { DefaultPolicyPack } from 'anchorai';
 *
 * // Use default policies
 * await anchor.config.update(agent.id, new DefaultPolicyPack().getConfig());
 *
 * // Customization (update default values / disable certain policies)
 * await anchor.config.update(agent.id, new DefaultPolicyPack({
 *   blockSecrets: false,
 *   maxQuerySize: null
 * }).getConfig());
 * ```
 */
export class DefaultPolicyPack {
    private config: DefaultPolicyPackConfig;

    constructor(config: DefaultPolicyPackConfig = {}) {
        this.config = config;
    }

    /**
     * Returns an object with configured policies to be used in `config`
     */
    getConfig(): { policies: Record<string, any> } {
        const policies: Record<string, any> = {};
        const { config } = this;

        if (Array.isArray(config.allowedDomains)) {
            policies.allowed_domains = config.allowedDomains;
        }

        const maxQuerySize =
            config.maxQuerySize === undefined
                ? DEFAULT_POLICY_CONFIG.maxQuerySize
                : config.maxQuerySize;

        if (maxQuerySize !== null) {
            policies.max_query_size = maxQuerySize;
        }

        const requireApprovalFor =
            config.requireApprovalFor === undefined
                ? DEFAULT_POLICY_CONFIG.requireApprovalFor
                : config.requireApprovalFor;

        if (requireApprovalFor !== null) {
            policies.require_approval_for = requireApprovalFor;
        }

        policies.block_pii = config.blockPii ?? DEFAULT_POLICY_CONFIG.blockPii;
        policies.block_secrets = config.blockSecrets ?? DEFAULT_POLICY_CONFIG.blockSecrets;

        return { policies };
    }
}