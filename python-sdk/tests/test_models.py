"""Tests for data models."""

import pytest
from datetime import datetime

from anchor.models import (
    Agent,
    Config,
    ConfigVersion,
    WriteResult,
    DataEntry,
    SearchResult,
    DataSnapshot,
    Checkpoint,
    RestoreResult,
    AuditEvent,
    Verification,
    ExportResult,
)
from anchor.policies import DefaultPolicyPack


class TestAgent:
    """Tests for Agent model."""

    def test_agent_creation(self):
        """Test creating an Agent from valid data."""
        data = {
            "id": "agent_123",
            "name": "test-agent",
            "status": "active",
            "metadata": {"env": "test"},
            "config_version": "v1",
            "data_count": 10,
            "checkpoint_count": 2,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        agent = Agent(**data)
        assert agent.id == "agent_123"
        assert agent.name == "test-agent"
        assert agent.status == "active"
        assert agent.metadata == {"env": "test"}
        assert agent.config_version == "v1"
        assert agent.data_count == 10
        assert agent.checkpoint_count == 2

    def test_agent_minimal(self):
        """Test Agent with minimal required fields."""
        data = {
            "id": "agent_123",
            "name": "test-agent",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        agent = Agent(**data)
        assert agent.metadata == {}
        assert agent.config_version is None
        assert agent.data_count is None
        assert agent.checkpoint_count is None

    def test_agent_datetime_parsing(self):
        """Test that datetime strings are parsed correctly."""
        data = {
            "id": "agent_123",
            "name": "test-agent",
            "status": "active",
            "created_at": "2024-01-01T12:30:45Z",
            "updated_at": "2024-01-01T12:30:45Z",
        }
        agent = Agent(**data)
        assert isinstance(agent.created_at, datetime)
        assert isinstance(agent.updated_at, datetime)


class TestConfig:
    """Tests for Config model."""

    def test_config_creation(self):
        """Test creating a Config from valid data."""
        data = {
            "agent_id": "agent_123",
            "version": "v1",
            "config": {
                "behavior": {"instructions": "Be helpful"},
                "policies": {"block_pii": True},
            },
            "previous_version": None,
            "created_at": "2024-01-01T00:00:00Z",
            "created_by": "user_123",
            "audit_id": "audit_123",
        }
        config = Config(**data)
        assert config.agent_id == "agent_123"
        assert config.version == "v1"
        assert config.config["behavior"]["instructions"] == "Be helpful"
        assert config.previous_version is None
        assert config.created_by == "user_123"
        assert config.audit_id == "audit_123"

    def test_config_minimal(self):
        """Test Config with minimal required fields."""
        data = {
            "agent_id": "agent_123",
            "version": "v1",
            "config": {},
            "created_at": "2024-01-01T00:00:00Z",
        }
        config = Config(**data)
        assert config.previous_version is None
        assert config.created_by is None
        assert config.audit_id is None


class TestConfigVersion:
    """Tests for ConfigVersion model."""

    def test_config_version_creation(self):
        """Test creating a ConfigVersion."""
        data = {
            "version": "v1",
            "created_at": "2024-01-01T00:00:00Z",
            "created_by": "user_123",
            "summary": "Initial config",
        }
        version = ConfigVersion(**data)
        assert version.version == "v1"
        assert version.created_by == "user_123"
        assert version.summary == "Initial config"

    def test_config_version_minimal(self):
        """Test ConfigVersion with minimal fields."""
        data = {
            "version": "v1",
            "created_at": "2024-01-01T00:00:00Z",
        }
        version = ConfigVersion(**data)
        assert version.created_by is None
        assert version.summary is None


class TestWriteResult:
    """Tests for WriteResult model."""

    def test_write_result_allowed(self):
        """Test WriteResult for allowed write."""
        data = {
            "key": "user:123:preference",
            "allowed": True,
            "audit_id": "audit_123",
        }
        result = WriteResult(**data)
        assert result.allowed is True
        assert result.blocked_by is None
        assert result.reason is None

    def test_write_result_blocked(self):
        """Test WriteResult for blocked write."""
        data = {
            "key": "user:123:email",
            "allowed": False,
            "audit_id": "audit_123",
            "blocked_by": "pii_filter",
            "reason": "Email addresses are not allowed",
        }
        result = WriteResult(**data)
        assert result.allowed is False
        assert result.blocked_by == "pii_filter"
        assert result.reason == "Email addresses are not allowed"


class TestDataEntry:
    """Tests for DataEntry model."""

    def test_data_entry_creation(self):
        """Test creating a DataEntry."""
        data = {
            "key": "user:123:preference",
            "value": "dark_mode",
            "metadata": {"source": "api"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "expires_at": "2025-01-01T00:00:00Z",
            "audit_id": "audit_123",
        }
        entry = DataEntry(**data)
        assert entry.key == "user:123:preference"
        assert entry.value == "dark_mode"
        assert entry.metadata == {"source": "api"}
        assert entry.expires_at is not None

    def test_data_entry_minimal(self):
        """Test DataEntry with minimal fields."""
        data = {
            "key": "user:123:preference",
            "value": "dark_mode",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "audit_id": "audit_123",
        }
        entry = DataEntry(**data)
        assert entry.metadata == {}
        assert entry.expires_at is None


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        data = {
            "key": "user:123:preference",
            "value": "dark_mode",
            "similarity": 0.95,
            "metadata": {"score": 0.95},
        }
        result = SearchResult(**data)
        assert result.similarity == 0.95
        assert result.metadata == {"score": 0.95}

    def test_search_result_minimal(self):
        """Test SearchResult with minimal fields."""
        data = {
            "key": "user:123:preference",
            "value": "dark_mode",
            "similarity": 0.85,
        }
        result = SearchResult(**data)
        assert result.metadata == {}


class TestDataSnapshot:
    """Tests for DataSnapshot model."""

    def test_data_snapshot_creation(self):
        """Test creating a DataSnapshot."""
        data = {"key_count": 100, "total_size_bytes": 10240}
        snapshot = DataSnapshot(**data)
        assert snapshot.key_count == 100
        assert snapshot.total_size_bytes == 10240


class TestCheckpoint:
    """Tests for Checkpoint model."""

    def test_checkpoint_creation(self):
        """Test creating a Checkpoint."""
        data = {
            "id": "checkpoint_123",
            "agent_id": "agent_123",
            "label": "v1.0",
            "description": "Pre-migration checkpoint",
            "config_version": "v1",
            "data_snapshot": {"key_count": 100, "total_size_bytes": 10240},
            "created_at": "2024-01-01T00:00:00Z",
            "audit_id": "audit_123",
        }
        checkpoint = Checkpoint(**data)
        assert checkpoint.id == "checkpoint_123"
        assert checkpoint.label == "v1.0"
        assert checkpoint.description == "Pre-migration checkpoint"
        assert checkpoint.data_snapshot.key_count == 100

    def test_checkpoint_minimal(self):
        """Test Checkpoint with minimal fields."""
        data = {
            "id": "checkpoint_123",
            "agent_id": "agent_123",
            "config_version": "v1",
            "data_snapshot": {"key_count": 0, "total_size_bytes": 0},
            "created_at": "2024-01-01T00:00:00Z",
        }
        checkpoint = Checkpoint(**data)
        assert checkpoint.label is None
        assert checkpoint.description is None
        assert checkpoint.audit_id is None


class TestRestoreResult:
    """Tests for RestoreResult model."""

    def test_restore_result_creation(self):
        """Test creating a RestoreResult."""
        data = {
            "restored_from": "checkpoint_123",
            "config_restored": True,
            "config_version": "v1",
            "data_restored": True,
            "data_keys_restored": 100,
            "data_keys_removed": 5,
            "audit_id": "audit_123",
            "restored_at": "2024-01-01T00:00:00Z",
        }
        result = RestoreResult(**data)
        assert result.config_restored is True
        assert result.data_restored is True
        assert result.data_keys_restored == 100
        assert result.data_keys_removed == 5


class TestAuditEvent:
    """Tests for AuditEvent model."""

    def test_audit_event_creation(self):
        """Test creating an AuditEvent."""
        data = {
            "id": "audit_123",
            "agent_id": "agent_123",
            "operation": "data.write",
            "resource": "user:123:preference",
            "result": "allowed",
            "blocked_by": None,
            "timestamp": "2024-01-01T00:00:00Z",
            "hash": "abc123def456",
            "previous_hash": "xyz789",
            "metadata": {"source": "api"},
        }
        event = AuditEvent(**data)
        assert event.operation == "data.write"
        assert event.result == "allowed"
        assert event.hash == "abc123def456"
        assert event.previous_hash == "xyz789"

    def test_audit_event_blocked(self):
        """Test AuditEvent for blocked operation."""
        data = {
            "id": "audit_123",
            "agent_id": "agent_123",
            "operation": "data.write",
            "resource": "user:123:email",
            "result": "blocked",
            "blocked_by": "pii_filter",
            "timestamp": "2024-01-01T00:00:00Z",
            "hash": "abc123def456",
            "previous_hash": None,
            "metadata": {},
        }
        event = AuditEvent(**data)
        assert event.result == "blocked"
        assert event.blocked_by == "pii_filter"
        assert event.previous_hash is None


class TestVerification:
    """Tests for Verification model."""

    def test_verification_valid(self):
        """Test Verification for valid chain."""
        data = {
            "valid": True,
            "events_checked": 100,
            "chain_start": "hash_start",
            "chain_end": "hash_end",
            "verified_at": "2024-01-01T00:00:00Z",
            "first_invalid": None,
        }
        verification = Verification(**data)
        assert verification.valid is True
        assert verification.events_checked == 100
        assert verification.first_invalid is None

    def test_verification_invalid(self):
        """Test Verification for invalid chain."""
        data = {
            "valid": False,
            "events_checked": 50,
            "chain_start": "hash_start",
            "chain_end": None,
            "verified_at": "2024-01-01T00:00:00Z",
            "first_invalid": {"id": "audit_50", "hash": "invalid_hash"},
        }
        verification = Verification(**data)
        assert verification.valid is False
        assert verification.events_checked == 50
        assert verification.first_invalid is not None


class TestExportResult:
    """Tests for ExportResult model."""

    def test_export_result_creation(self):
        """Test creating an ExportResult."""
        data = {
            "export_id": "export_123",
            "format": "json",
            "download_url": "https://api.getanchor.dev/exports/export_123",
            "expires_at": "2024-01-02T00:00:00Z",
            "event_count": 1000,
            "verification": {
                "valid": True,
                "events_checked": 1000,
                "verified_at": "2024-01-01T00:00:00Z",
            },
        }
        export = ExportResult(**data)
        assert export.export_id == "export_123"
        assert export.format == "json"
        assert export.event_count == 1000
        assert export.verification is not None
        assert export.verification.valid is True

    def test_export_result_minimal(self):
        """Test ExportResult with minimal fields."""
        data = {
            "export_id": "export_123",
            "format": "csv",
            "download_url": "https://api.getanchor.dev/exports/export_123",
            "expires_at": "2024-01-02T00:00:00Z",
            "event_count": 100,
        }
        export = ExportResult(**data)
        assert export.verification is None


class TestModelValidation:
    """Tests for model validation and error handling."""

    def test_agent_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Agent(
                id="agent_123",
                name="test-agent",
                # Missing status, created_at, updated_at
            )

    def test_write_result_type_validation(self):
        """Test that boolean fields are validated."""
        # Pydantic will coerce truthy strings to bool, so use None which will fail
        with pytest.raises(Exception):  # Pydantic ValidationError
            WriteResult(
                key="test",
                allowed=None,  # Should be bool, not None
                audit_id="audit_123",
            )

    def test_search_result_similarity_range(self):
        """Test that similarity is a float."""
        # Pydantic will accept int and convert to float
        result = SearchResult(
            key="test", value="test", similarity=1
        )  # int 1 should work
        assert isinstance(result.similarity, (int, float))

    def test_model_serialization(self):
        """Test that models can be serialized to dict."""
        agent = Agent(
            id="agent_123",
            name="test-agent",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        data = agent.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == "agent_123"
        assert data["name"] == "test-agent"

    def test_model_json_serialization(self):
        """Test that models can be serialized to JSON."""
        agent = Agent(
            id="agent_123",
            name="test-agent",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        json_str = agent.model_dump_json()
        assert isinstance(json_str, str)
        assert "agent_123" in json_str


class TestPolicies:
    """Tests for DefaultPolicyPack model."""

    def test_default_policy_pack_defaults(self):
        """Test DefaultPolicyPack with default values."""
        pack = DefaultPolicyPack()
        config = pack.get_config()

        policies = config["policies"]

        assert policies["max_query_size"] == 1000
        assert policies["block_pii"] is True
        assert policies["block_secrets"] is True
        assert policies["require_approval_for"] == ["delete", "update", "export"]
        assert "allowed_domains" not in policies

    def test_default_policy_pack_custom_values(self):
        """Test DefaultPolicyPack with custom values."""
        pack = DefaultPolicyPack(
            allowed_domains=["example.com"],
            max_query_size=500,
            require_approval_for=["delete"],
            block_pii=False,
            block_secrets=False,
        )
        config = pack.get_config()
        policies = config["policies"]

        assert policies["allowed_domains"] == ["example.com"]
        assert policies["max_query_size"] == 500
        assert policies["require_approval_for"] == ["delete"]
        assert policies["block_pii"] is False
        assert policies["block_secrets"] is False

    def test_default_policy_pack_disable_optional(self):
        """Test disabling optional policies with None."""
        pack = DefaultPolicyPack(max_query_size=None, require_approval_for=None)
        config = pack.get_config()
        policies = config["policies"]

        assert "max_query_size" not in policies
        assert "require_approval_for" not in policies

        assert policies["block_pii"] is True
        assert policies["block_secrets"] is True

