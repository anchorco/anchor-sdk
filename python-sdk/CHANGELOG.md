# Changelog

All notable changes to the Anchor SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## 2025-01-08

### Added
- `workspace_id` parameter support in `Anchor.__init__()` and `ClientConfig`
- Automatic `workspaceId` injection in all API requests (POST/PUT/PATCH in body, GET/DELETE in query params)
- `workspace_id` parameter in `agents.create()` method (optional override)
- `get_workspace_id()` helper method to fetch default workspace ID from API
- Warning when `workspace_id` is not provided (to prevent data mixing issues)

### Changed
- All API calls now automatically include `workspaceId` if set during client initialization
- `HttpClient.request()` now accepts optional `workspace_id` parameter for per-request overrides

### Fixed
- Resolves `ValidationError: workspaceId is required` when creating agents and other operations
- Prevents data mixing issues by requiring explicit workspace_id

## [1.0.0] - 2025-12-30

### Added

- Initial public release of Anchor Python SDK
- `Anchor` client with five namespaces:
  - `anchor.agents` – Create, get, list, update, delete, suspend, activate agents
  - `anchor.config` – Get, update, list versions, rollback configuration
  - `anchor.data` – Write, read, search, delete key-value data with policy enforcement
  - `anchor.checkpoints` – Create, list, get, restore, delete state snapshots
  - `anchor.audit` – Query events, verify chain integrity, export for compliance
- Policy enforcement on write (block PII, secrets, custom patterns)
- Hash-chained audit logging
- Custom exceptions:
  - `AnchorError` – Base exception
  - `AuthenticationError` – Invalid API key
  - `NotFoundError` – Resource not found
  - `ValidationError` – Invalid input
  - `PolicyViolationError` – Blocked by policy
  - `RateLimitError` – Rate limit exceeded
- Automatic retry with exponential backoff
- Full type hints

[1.0.0]: https://github.com/anchorco/sdk/releases/tag/v1.0.0