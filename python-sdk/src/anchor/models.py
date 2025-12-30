"""Data models returned by Anchor SDK methods."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class Agent(BaseModel):
    """Agent model."""

    id: str
    name: str
    status: str  # "active" | "suspended"
    metadata: Dict[str, Any] = {}
    config_version: Optional[str] = None
    data_count: Optional[int] = None
    checkpoint_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class Config(BaseModel):
    """Agent configuration model."""

    agent_id: str
    version: str
    config: Dict[str, Any]  # e.g., { behavior: {...}, policies: {...} }
    previous_version: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    audit_id: Optional[str] = None


class ConfigVersion(BaseModel):
    """Config version summary."""

    version: str
    created_at: datetime
    created_by: Optional[str] = None
    summary: Optional[str] = None


class WriteResult(BaseModel):
    """Result of a data write operation."""

    key: str
    allowed: bool
    audit_id: str
    blocked_by: Optional[str] = None  # e.g., "policy:block_pii"
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class DataEntry(BaseModel):
    """Full data entry with metadata."""

    key: str
    value: str
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    audit_id: str


class SearchResult(BaseModel):
    """Search result with similarity score."""

    key: str
    value: str
    similarity: float  # 0.0 - 1.0
    metadata: Dict[str, Any] = {}


class DataSnapshot(BaseModel):
    """Data snapshot info in checkpoint."""

    key_count: int
    total_size_bytes: int


class Checkpoint(BaseModel):
    """Checkpoint model."""

    id: str
    agent_id: str
    label: Optional[str] = None
    description: Optional[str] = None
    config_version: str
    data_snapshot: DataSnapshot
    created_at: datetime
    audit_id: Optional[str] = None


class RestoreResult(BaseModel):
    """Result of checkpoint restore."""

    restored_from: str
    config_restored: bool
    config_version: Optional[str] = None
    data_restored: bool
    data_keys_restored: int
    data_keys_removed: int
    audit_id: str
    restored_at: datetime


class AuditEvent(BaseModel):
    """Audit event model."""

    id: str
    agent_id: str
    operation: str  # e.g., # "data.write", "data.delete", "config.update", "checkpoint.create", "checkpoint.restore"
    resource: str  # e.g., "user:123:preference"
    result: str  # "allowed" | "blocked"
    blocked_by: Optional[str] = None
    timestamp: datetime
    hash: str  # sha256 hash
    previous_hash: Optional[str] = None
    metadata: Dict[str, Any] = {}


class Verification(BaseModel):
    """Audit chain verification result."""

    valid: bool
    events_checked: int
    chain_start: Optional[str] = None
    chain_end: Optional[str] = None
    verified_at: datetime
    first_invalid: Optional[Dict[str, Any]] = None


class ExportResult(BaseModel):
    """Audit export result."""

    export_id: str
    format: str
    download_url: str
    expires_at: datetime
    event_count: int
    verification: Optional[Verification] = None
