"""Tests for Anchor SDK with 5 namespaces (agents, config, data, checkpoints, audit)"""

import pytest
from unittest.mock import patch

from anchor import Anchor, Agent, Config
from anchor import WriteResult
from anchor import Checkpoint, RestoreResult
from anchor import AuditEvent, Verification, ExportResult
from anchor.exceptions import NotFoundError


class TestAnchorClient:
    """Tests for the main Anchor client."""

    def test_initialization_with_api_key(self):
        """Test client initialization with API key."""
        anchor = Anchor(api_key="anc_test_key")
        assert anchor.client_config.api_key == "anc_test_key"
        assert anchor.client_config.base_url == "https://api.getanchor.dev"

    def test_initialization_requires_api_key(self):
        """Test that initialization fails without API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            Anchor()

    def test_namespaces_available(self):
        """Test that all 5 namespaces are available."""
        anchor = Anchor(api_key="anc_test_key")
        assert hasattr(anchor, "agents")
        assert hasattr(anchor, "config")
        assert hasattr(anchor, "data")
        assert hasattr(anchor, "checkpoints")
        assert hasattr(anchor, "audit")

    def test_initialization_with_workspace_id(self):
        """Test client initialization with workspace_id."""
        anchor = Anchor(api_key="anc_test_key", workspace_id="workspace-123")
        assert anchor.client_config.api_key == "anc_test_key"
        assert anchor.client_config.workspace_id == "workspace-123"

    def test_get_workspace_id_from_config(self):
        """Test get_workspace_id returns workspace_id from config."""
        anchor = Anchor(api_key="anc_test_key", workspace_id="workspace-123")
        assert anchor.get_workspace_id() == "workspace-123"

    def test_get_workspace_id_from_api(self):
        """Test get_workspace_id fetches from API when not in config."""
        anchor = Anchor(api_key="anc_test_key")
        with patch.object(anchor._http, "get") as mock_get:
            mock_get.return_value = {
                "workspaces": [{"id": "workspace-456"}]
            }
            workspace_id = anchor.get_workspace_id()
            assert workspace_id == "workspace-456"
            mock_get.assert_called_once_with("/workspaces")

    def test_get_workspace_id_returns_none_on_error(self):
        """Test get_workspace_id returns None when API call fails."""
        anchor = Anchor(api_key="anc_test_key")
        with patch.object(anchor._http, "get", side_effect=Exception("API error")):
            workspace_id = anchor.get_workspace_id()
            assert workspace_id is None


class TestAgentsNamespace:
    """Tests for agents namespace."""

    @pytest.fixture
    def anchor(self):
        return Anchor(api_key="anc_test_key")

    @pytest.fixture
    def mock_http(self, anchor):
        with patch.object(anchor._http, "post") as mock_post, patch.object(
            anchor._http, "get"
        ) as mock_get, patch.object(anchor._http, "patch") as mock_patch, patch.object(
            anchor._http, "delete"
        ) as mock_delete:
            yield {
                "post": mock_post,
                "get": mock_get,
                "patch": mock_patch,
                "delete": mock_delete,
            }

    def test_create_agent(self, anchor, mock_http):
        """Test creating an agent."""
        mock_http["post"].return_value = {
            "agent": {
                "id": "agent_123",
                "name": "test-agent",
                "status": "active",
                "metadata": {},
                "created_at": "2024-01-01T00:00:00Z",
            }
        }

        agent = anchor.agents.create("test-agent", {"env": "test"})

        assert isinstance(agent, Agent)
        assert agent.id == "agent_123"
        assert agent.name == "test-agent"
        assert agent.status == "active"

    def test_create_agent_with_workspace_id_override(self, anchor, mock_http):
        """Test creating an agent with workspace_id override."""
        mock_http["post"].return_value = {
            "agent": {
                "id": "agent_123",
                "name": "test-agent",
                "status": "active",
                "metadata": {},
            }
        }

        agent = anchor.agents.create("test-agent", workspace_id="workspace-999")

        assert isinstance(agent, Agent)
        # Verify workspace_id was passed to HTTP client
        call_args = mock_http["post"].call_args
        assert call_args[1]["workspace_id"] == "workspace-999"

    def test_get_agent(self, anchor, mock_http):
        """Test getting an agent."""
        mock_http["get"].return_value = {
            "agent": {"id": "agent_123", "name": "test-agent", "status": "active"}
        }

        agent = anchor.agents.get("agent_123")

        assert agent.id == "agent_123"

    def test_list_agents(self, anchor, mock_http):
        """Test listing agents."""
        mock_http["get"].return_value = {
            "agents": [
                {"id": "agent_1", "name": "agent-1", "status": "active"},
                {"id": "agent_2", "name": "agent-2", "status": "suspended"},
            ]
        }

        agents = anchor.agents.list()

        assert len(agents) == 2
        assert agents[0].id == "agent_1"

    def test_suspend_agent(self, anchor, mock_http):
        """Test suspending an agent uses POST."""
        mock_http["post"].return_value = {
            "agent": {"id": "agent_123", "name": "test", "status": "suspended"}
        }

        agent = anchor.agents.suspend("agent_123")

        assert agent.status == "suspended"
        mock_http["post"].assert_called_once()

    def test_activate_agent(self, anchor, mock_http):
        """Test activating an agent uses POST."""
        mock_http["post"].return_value = {
            "agent": {"id": "agent_123", "name": "test", "status": "active"}
        }

        agent = anchor.agents.activate("agent_123")

        assert agent.status == "active"
        mock_http["post"].assert_called_once()


class TestConfigNamespace:
    """Tests for config namespace."""

    @pytest.fixture
    def anchor(self):
        return Anchor(api_key="anc_test_key")

    @pytest.fixture
    def mock_http(self, anchor):
        with patch.object(anchor._http, "get") as mock_get, patch.object(
            anchor._http, "put"
        ) as mock_put, patch.object(anchor._http, "post") as mock_post:
            yield {"get": mock_get, "put": mock_put, "post": mock_post}

    def test_get_config(self, anchor, mock_http):
        """Test getting config."""
        mock_http["get"].return_value = {
            "agent_id": "agent_123",
            "version": "v1",
            "config": {
                "instructions": "Be helpful",  # Freeform field
                "model": "gpt-4",
                "policies": {"block_pii": True},
            },
        }

        config = anchor.config.get("agent_123")

        assert isinstance(config, Config)
        assert config.version == "v1"
        assert config.config["instructions"] == "Be helpful"

    def test_update_config(self, anchor, mock_http):
        """Test updating config - schema-less with policies."""
        mock_http["put"].return_value = {
            "agent_id": "agent_123",
            "version": "v2",
            "config": {
                "role": "Support Agent",  # CrewAI-style
                "goal": "Help users",
                "policies": {"block_pii": True, "block_secrets": True}
            },
        }

        config = anchor.config.update(
            "agent_123", {
                "role": "Support Agent",
                "goal": "Help users",
                "policies": {"block_pii": True, "block_secrets": True}
            }
        )

        assert config.version == "v2"


class TestDataNamespace:
    """Tests for data namespace."""

    @pytest.fixture
    def anchor(self):
        return Anchor(api_key="anc_test_key")

    @pytest.fixture
    def mock_http(self, anchor):
        with patch.object(anchor._http, "post") as mock_post, patch.object(
            anchor._http, "get"
        ) as mock_get, patch.object(anchor._http, "delete") as mock_delete:
            yield {"post": mock_post, "get": mock_get, "delete": mock_delete}

    def test_write_data(self, anchor, mock_http):
        """Test writing data."""
        mock_http["post"].return_value = {
            "key": "user:123:pref",
            "allowed": True,
            "audit_id": "audit_abc",
        }

        result = anchor.data.write("agent_123", "user:123:pref", "dark_mode")

        assert isinstance(result, WriteResult)
        assert result.key == "user:123:pref"
        assert result.allowed is True

    def test_write_blocked_by_policy(self, anchor, mock_http):
        """Test write blocked by policy."""
        mock_http["post"].return_value = {
            "key": "user:123:ssn",
            "allowed": False,
            "blocked_by": "pii_filter",
            "reason": "SSN detected",
            "audit_id": "audit_def",
        }

        result = anchor.data.write("agent_123", "user:123:ssn", "123-45-6789")

        assert result.allowed is False
        assert result.blocked_by == "pii_filter"

    def test_read_data(self, anchor, mock_http):
        """Test reading data."""
        mock_http["get"].return_value = {"value": "dark_mode"}

        value = anchor.data.read("agent_123", "user:123:pref")

        assert value == "dark_mode"

    def test_read_not_found(self, anchor, mock_http):
        """Test reading non-existent data returns None."""
        mock_http["get"].side_effect = NotFoundError("Data", "key")

        value = anchor.data.read("agent_123", "nonexistent")

        assert value is None


class TestCheckpointsNamespace:
    """Tests for checkpoints namespace."""

    @pytest.fixture
    def anchor(self):
        return Anchor(api_key="anc_test_key")

    @pytest.fixture
    def mock_http(self, anchor):
        with patch.object(anchor._http, "post") as mock_post, patch.object(
            anchor._http, "get"
        ) as mock_get, patch.object(anchor._http, "delete") as mock_delete:
            yield {"post": mock_post, "get": mock_get, "delete": mock_delete}

    def test_create_checkpoint(self, anchor, mock_http):
        """Test creating a checkpoint."""
        mock_http["post"].return_value = {
            "id": "cp_123",
            "agent_id": "agent_123",
            "label": "v1.0",
            "config_version": "v5",
            "created_at": "2024-01-01T00:00:00Z",
        }

        checkpoint = anchor.checkpoints.create("agent_123", label="v1.0")

        assert isinstance(checkpoint, Checkpoint)
        assert checkpoint.id == "cp_123"
        assert checkpoint.label == "v1.0"

    def test_restore_checkpoint(self, anchor, mock_http):
        """Test restoring from a checkpoint."""
        mock_http["post"].return_value = {
            "restored_from": "cp_123",
            "config_restored": True,
            "config_version": "v5",
            "data_restored": True,
            "data_keys_restored": 50,
            "data_keys_removed": 10,
            "audit_id": "audit_xyz",
        }

        result = anchor.checkpoints.restore("agent_123", "cp_123")

        assert isinstance(result, RestoreResult)
        assert result.config_restored is True
        assert result.data_keys_restored == 50


class TestAuditNamespace:
    """Tests for audit namespace."""

    @pytest.fixture
    def anchor(self):
        return Anchor(api_key="anc_test_key")

    @pytest.fixture
    def mock_http(self, anchor):
        with patch.object(anchor._http, "get") as mock_get, patch.object(
            anchor._http, "post"
        ) as mock_post:
            yield {"get": mock_get, "post": mock_post}

    def test_query_audit_events(self, anchor, mock_http):
        """Test querying audit events."""
        mock_http["get"].return_value = {
            "events": [
                {
                    "id": "audit_1",
                    "agent_id": "agent_123",
                    "operation": "data.write",
                    "resource": "user:123:pref",
                    "result": "allowed",
                    "hash": "abc123",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            ]
        }

        events = anchor.audit.query("agent_123", operations=["data.write"])

        assert len(events) == 1
        assert isinstance(events[0], AuditEvent)
        assert events[0].operation == "data.write"

    def test_verify_chain(self, anchor, mock_http):
        """Test verifying audit chain."""
        mock_http["get"].return_value = {
            "valid": True,
            "events_checked": 100,
            "chain_start": "audit_001",
            "chain_end": "audit_100",
        }

        verification = anchor.audit.verify("agent_123")

        assert isinstance(verification, Verification)
        assert verification.valid is True
        assert verification.events_checked == 100

    def test_export_audit(self, anchor, mock_http):
        """Test exporting audit trail."""
        mock_http["post"].return_value = {
            "export_id": "exp_123",
            "format": "json",
            "download_url": "https://example.com/download",
            "event_count": 100,
        }

        result = anchor.audit.export("agent_123", format="json")

        assert isinstance(result, ExportResult)
        assert result.format == "json"
        assert result.event_count == 100
