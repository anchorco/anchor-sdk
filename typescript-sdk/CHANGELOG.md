# Changelog

All notable changes to the Anchor SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## 2025-01-08

### Added
- `workspaceId` parameter support in `Anchor` constructor and `Config` interface
- Automatic `workspaceId` injection in all API requests (POST/PUT/PATCH in body, GET/DELETE in query params)
- `workspaceId` parameter in `agents.create()` method (optional override)
- `getWorkspaceId()` helper method to fetch default workspace ID from API
- Warning when `workspaceId` is not provided (to prevent data mixing issues)

### Changed
- All API calls now automatically include `workspaceId` if set during client initialization
- `HttpClient.request()` now accepts optional `workspaceId` parameter for per-request overrides
- User-Agent updated to `anchorai-typescript/1.0.1`

### Fixed
- Resolves `ValidationError: workspaceId is required` when creating agents and other operations
- Prevents data mixing issues by requiring explicit workspaceId

## [1.0.0] - 2025-12-30

### Added

- Initial public release of Anchor TypeScript SDK
- `Anchor` client with five namespaces:
  - `anchor.agents` - Create, get, list, update, delete, suspend, activate agents
  - `anchor.config` - Get, update, list versions, rollback configuration
  - `anchor.data` - Write, read, search, delete key-value data with policy enforcement
  - `anchor.checkpoints` - Create, list, get, restore, delete state snapshots
  - `anchor.audit` - Query events, verify chain integrity, export for compliance
- Policy enforcement on write (block PII, secrets, custom patterns)
- Hash-chained audit logging
- Custom exceptions:
  - `AnchorError` - Base exception
  - `AuthenticationError` - Invalid API key
  - `NotFoundError` - Resource not found
  - `ValidationError` - Invalid input
  - `PolicyViolationError` - Blocked by policy
  - `RateLimitError` - Rate limit exceeded
- Automatic retry with exponential backoff
- Full TypeScript type definitions
- Framework integrations:
  - LangChain: `AnchorMemory`, `AnchorChatHistory`
  - CrewAI: `AnchorCrewAgent`, `AnchorCrewMemory`
  - Mem0: `AnchorMem0`

[1.0.0]: https://github.com/anchorco/sdk/releases/tag/v1.0.0
