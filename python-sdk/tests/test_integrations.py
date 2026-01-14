"""Tests for framework integrations."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from anchor import Anchor
from anchor.models import WriteResult, DataEntry


class TestIntegrationsInit:
    """Tests for integrations __init__.py lazy loading."""

    def test_lazy_import_langchain(self):
        """Test that langchain integration can be imported."""
        # Direct import should work
        from anchor.integrations.langchain import AnchorMemory, AnchorChatHistory

        assert AnchorMemory is not None
        assert AnchorChatHistory is not None

    def test_lazy_import_crewai(self):
        """Test that crewai integration can be imported."""
        # Direct import should work
        from anchor.integrations.crewai import AnchorCrewAgent, AnchorCrewMemory

        assert AnchorCrewAgent is not None
        assert AnchorCrewMemory is not None

    def test_lazy_import_mem0(self):
        """Test that mem0 integration can be imported."""
        # Direct import should work
        from anchor.integrations.mem0 import AnchorMem0

        assert AnchorMem0 is not None

    def test_integrations_module_has_getattr(self):
        """Test that integrations module has __getattr__ for lazy loading."""
        import anchor.integrations as integrations

        # Test that __getattr__ exists (implementation detail)
        assert hasattr(integrations, "__getattr__")


class TestLangChainIntegration:
    """Tests for LangChain integration."""

    @pytest.fixture
    def anchor(self):
        """Create a mock Anchor client."""
        anchor = Mock(spec=Anchor)
        anchor.agents = Mock()
        anchor.data = Mock()
        anchor.checkpoints = Mock()
        anchor.config = Mock()
        return anchor

    @pytest.fixture
    def agent_id(self):
        """Return a test agent ID."""
        return "agent_123"

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    @patch("anchor.integrations.langchain.HumanMessage")
    @patch("anchor.integrations.langchain.AIMessage")
    @patch("anchor.integrations.langchain.SystemMessage")
    def test_anchor_memory_initialization(
        self, mock_system, mock_ai, mock_human, anchor, agent_id
    ):
        """Test AnchorMemory initialization."""
        from anchor.integrations.langchain import AnchorMemory

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id)
        assert memory.anchor == anchor
        assert memory.agent_id == agent_id
        assert memory.memory_key == "chat_history"
        assert memory.return_messages is True
        assert memory.session_id is not None

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    def test_anchor_memory_custom_params(self, anchor, agent_id):
        """Test AnchorMemory with custom parameters."""
        from anchor.integrations.langchain import AnchorMemory

        memory = AnchorMemory(
            anchor=anchor,
            agent_id=agent_id,
            memory_key="history",
            return_messages=False,
            session_id="custom_session",
        )
        assert memory.memory_key == "history"
        assert memory.return_messages is False
        assert memory.session_id == "custom_session"

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    def test_anchor_memory_memory_variables(self, anchor, agent_id):
        """Test memory_variables property."""
        from anchor.integrations.langchain import AnchorMemory

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id, memory_key="history")
        assert memory.memory_variables == ["history"]

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    @patch("anchor.integrations.langchain.HumanMessage")
    @patch("anchor.integrations.langchain.AIMessage")
    def test_anchor_memory_save_context(
        self, mock_ai, mock_human, anchor, agent_id
    ):
        """Test saving context to Anchor."""
        from anchor.integrations.langchain import AnchorMemory

        # Mock write results
        anchor.data.write.return_value = WriteResult(
            key="test", allowed=True, audit_id="audit_123"
        )

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id, session_id="test_session")
        memory.save_context(
            inputs={"input": "Hello"}, outputs={"output": "Hi there"}
        )

        # Should have called write twice (for input and output)
        assert anchor.data.write.call_count == 2

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    @patch("anchor.integrations.langchain.HumanMessage")
    @patch("anchor.integrations.langchain.AIMessage")
    def test_anchor_memory_load_memory_variables(
        self, mock_ai, mock_human, anchor, agent_id
    ):
        """Test loading memory variables."""
        from anchor.integrations.langchain import AnchorMemory

        # Mock list and read_full
        anchor.data.list.return_value = ["chat:test:human:1", "chat:test:ai:2"]

        # Create mock entries
        human_entry = DataEntry(
            key="chat:test:human:1",
            value="Hello",
            metadata={"role": "human"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            audit_id="audit_123",
        )
        ai_entry = DataEntry(
            key="chat:test:ai:2",
            value="Hi there",
            metadata={"role": "ai"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            audit_id="audit_123",
        )

        def read_full_side_effect(agent_id, key):
            if "human" in key:
                return human_entry
            return ai_entry

        anchor.data.read_full.side_effect = read_full_side_effect

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id, session_id="test")
        result = memory.load_memory_variables({})

        assert memory.memory_key in result
        anchor.data.list.assert_called_once()

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    def test_anchor_memory_clear(self, anchor, agent_id):
        """Test clearing memory."""
        from anchor.integrations.langchain import AnchorMemory

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id, session_id="test")
        memory.clear()

        assert len(memory._messages) == 0
        anchor.data.delete_prefix.assert_called_once_with(
            agent_id, "chat:test:"
        )

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    def test_anchor_memory_create_checkpoint(self, anchor, agent_id):
        """Test creating checkpoint."""
        from anchor.integrations.langchain import AnchorMemory
        from anchor.models import Checkpoint, DataSnapshot

        mock_checkpoint = Checkpoint(
            id="checkpoint_123",
            agent_id=agent_id,
            config_version="v1",
            data_snapshot=DataSnapshot(key_count=10, total_size_bytes=1024),
            created_at=datetime.now(timezone.utc),
        )
        anchor.checkpoints.create.return_value = mock_checkpoint

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id, session_id="test")
        checkpoint_id = memory.create_checkpoint(label="test-checkpoint")

        assert checkpoint_id == "checkpoint_123"
        anchor.checkpoints.create.assert_called_once()

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    @patch("anchor.integrations.langchain.AnchorMemory._load_from_anchor")
    def test_anchor_memory_restore_checkpoint(self, mock_load, anchor, agent_id):
        """Test restoring checkpoint."""
        from anchor.integrations.langchain import AnchorMemory

        memory = AnchorMemory(anchor=anchor, agent_id=agent_id, session_id="test")
        memory.restore_checkpoint("checkpoint_123")

        anchor.checkpoints.restore.assert_called_once_with(agent_id, "checkpoint_123")
        mock_load.assert_called_once()

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", False)
    def test_anchor_memory_without_langchain(self, anchor, agent_id):
        """Test AnchorMemory when LangChain is not available."""
        from anchor.integrations.langchain import AnchorMemory

        # Should still work, just won't use LangChain message types
        memory = AnchorMemory(anchor=anchor, agent_id=agent_id)
        assert memory.anchor == anchor

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", True)
    @patch("anchor.integrations.langchain.BaseChatMessageHistory")
    def test_anchor_chat_history_initialization(
        self, mock_base, anchor, agent_id
    ):
        """Test AnchorChatHistory initialization."""
        from anchor.integrations.langchain import AnchorChatHistory

        history = AnchorChatHistory(anchor=anchor, agent_id=agent_id)
        assert history.anchor == anchor
        assert history.agent_id == agent_id

    @patch("anchor.integrations.langchain.LANGCHAIN_AVAILABLE", False)
    def test_anchor_chat_history_without_langchain(self, anchor, agent_id):
        """Test AnchorChatHistory when LangChain is not available."""
        from anchor.integrations.langchain import AnchorChatHistory

        with pytest.raises(ImportError):
            AnchorChatHistory(anchor=anchor, agent_id=agent_id)


class TestCrewAIIntegration:
    """Tests for CrewAI integration."""

    @pytest.fixture
    def anchor(self):
        """Create a mock Anchor client."""
        anchor = Mock(spec=Anchor)
        anchor.agents = Mock()
        anchor.data = Mock()
        anchor.config = Mock()
        return anchor

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    @patch("anchor.integrations.crewai.Agent")
    def test_anchor_crew_agent_initialization(self, mock_agent_class, anchor):
        """Test AnchorCrewAgent initialization."""
        from anchor.integrations.crewai import AnchorCrewAgent

        # Mock agent creation
        mock_anchor_agent = Mock()
        mock_anchor_agent.id = "agent_123"
        anchor.agents.create.return_value = mock_anchor_agent

        # Mock CrewAI agent
        mock_crew_agent = Mock()
        mock_agent_class.return_value = mock_crew_agent

        crew_agent = AnchorCrewAgent(
            anchor=anchor, role="Researcher", goal="Research topics"
        )

        assert crew_agent.anchor == anchor
        assert crew_agent.role == "Researcher"
        assert crew_agent.goal == "Research topics"
        assert crew_agent.agent_id == "agent_123"
        assert crew_agent.agent == mock_crew_agent

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    @patch("anchor.integrations.crewai.Agent")
    def test_anchor_crew_agent_store(self, mock_agent_class, anchor):
        """Test storing data."""
        from anchor.integrations.crewai import AnchorCrewAgent

        mock_anchor_agent = Mock()
        mock_anchor_agent.id = "agent_123"
        anchor.agents.create.return_value = mock_anchor_agent
        mock_agent_class.return_value = Mock()

        anchor.data.write.return_value = WriteResult(
            key="test", allowed=True, audit_id="audit_123"
        )

        crew_agent = AnchorCrewAgent(
            anchor=anchor, role="Researcher", goal="Research"
        )
        result = crew_agent.store("key1", "value1", metadata={"source": "test"})

        assert result is True
        anchor.data.write.assert_called_once()

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    @patch("anchor.integrations.crewai.Agent")
    def test_anchor_crew_agent_retrieve(self, mock_agent_class, anchor):
        """Test retrieving data."""
        from anchor.integrations.crewai import AnchorCrewAgent

        mock_anchor_agent = Mock()
        mock_anchor_agent.id = "agent_123"
        anchor.agents.create.return_value = mock_anchor_agent
        mock_agent_class.return_value = Mock()

        anchor.data.read.return_value = "stored_value"

        crew_agent = AnchorCrewAgent(anchor=anchor, role="Researcher", goal="Research")
        result = crew_agent.retrieve("key1")

        assert result == "stored_value"
        anchor.data.read.assert_called_once_with("agent_123", "key1")

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    @patch("anchor.integrations.crewai.Agent")
    def test_anchor_crew_agent_search(self, mock_agent_class, anchor):
        """Test searching data."""
        from anchor.integrations.crewai import AnchorCrewAgent
        from anchor.models import SearchResult

        mock_anchor_agent = Mock()
        mock_anchor_agent.id = "agent_123"
        anchor.agents.create.return_value = mock_anchor_agent
        mock_agent_class.return_value = Mock()

        mock_results = [
            SearchResult(key="k1", value="v1", similarity=0.9),
            SearchResult(key="k2", value="v2", similarity=0.8),
        ]
        anchor.data.search.return_value = mock_results

        crew_agent = AnchorCrewAgent(anchor=anchor, role="Researcher", goal="Research")
        results = crew_agent.search("query", limit=5)

        assert len(results) == 2
        assert results[0]["key"] == "k1"
        assert results[0]["similarity"] == 0.9

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    def test_anchor_crew_memory_initialization(self, anchor):
        """Test AnchorCrewMemory initialization."""
        from anchor.integrations.crewai import AnchorCrewMemory

        mock_agent = Mock()
        mock_agent.id = "agent_123"
        anchor.agents.create.return_value = mock_agent

        memory = AnchorCrewMemory(anchor=anchor)
        assert memory.anchor == anchor
        assert memory.agent_id == "agent_123"

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    def test_anchor_crew_memory_with_agent_id(self, anchor):
        """Test AnchorCrewMemory with existing agent ID."""
        from anchor.integrations.crewai import AnchorCrewMemory

        memory = AnchorCrewMemory(anchor=anchor, agent_id="existing_agent")
        assert memory.agent_id == "existing_agent"
        anchor.agents.create.assert_not_called()

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", True)
    def test_anchor_crew_memory_save(self, anchor):
        """Test saving to memory."""
        from anchor.integrations.crewai import AnchorCrewMemory

        mock_agent = Mock()
        mock_agent.id = "agent_123"
        anchor.agents.create.return_value = mock_agent

        anchor.data.write.return_value = WriteResult(
            key="test", allowed=True, audit_id="audit_123"
        )

        memory = AnchorCrewMemory(anchor=anchor)
        result = memory.save("key1", "value1")

        assert result is True
        anchor.data.write.assert_called_once()

    @patch("anchor.integrations.crewai.CREWAI_AVAILABLE", False)
    def test_anchor_crew_agent_without_crewai(self, anchor):
        """Test AnchorCrewAgent when CrewAI is not available."""
        from anchor.integrations.crewai import AnchorCrewAgent

        with pytest.raises(ImportError, match="CrewAI is required"):
            AnchorCrewAgent(anchor=anchor, role="Researcher", goal="Research")


class TestMem0Integration:
    """Tests for Mem0 integration."""

    @pytest.fixture
    def anchor(self):
        """Create a mock Anchor client."""
        anchor = Mock(spec=Anchor)
        anchor.data = Mock()
        return anchor

    @pytest.fixture
    def agent_id(self):
        """Return a test agent ID."""
        return "agent_123"

    @pytest.fixture
    def mock_mem0(self):
        """Create a mock Mem0 client."""
        mem0 = Mock()
        mem0.add = Mock(return_value={"id": "mem_123"})
        mem0.search = Mock(return_value=[{"id": "mem_123", "content": "test"}])
        mem0.get = Mock(return_value={"id": "mem_123", "content": "test"})
        mem0.get_all = Mock(return_value=[{"id": "mem_123"}])
        mem0.update = Mock(return_value={"id": "mem_123"})
        mem0.delete = Mock(return_value=True)
        return mem0

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_initialization(self, anchor, agent_id, mock_mem0):
        """Test AnchorMem0 initialization."""
        from anchor.integrations.mem0 import AnchorMem0

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        assert wrapped.anchor == anchor
        assert wrapped.agent_id == agent_id
        assert wrapped.mem0 == mock_mem0

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_add_allowed(self, anchor, agent_id, mock_mem0):
        """Test adding memory when allowed."""
        from anchor.integrations.mem0 import AnchorMem0

        anchor.data.write.return_value = WriteResult(
            key="test", allowed=True, audit_id="audit_123"
        )

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        result = wrapped.add("User prefers dark mode", user_id="user_123")

        assert result.allowed is True
        assert result.blocked_by is None
        assert result.mem0_result == {"id": "mem_123"}
        mock_mem0.add.assert_called_once()

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_add_blocked(self, anchor, agent_id, mock_mem0):
        """Test adding memory when blocked by policy."""
        from anchor.integrations.mem0 import AnchorMem0

        anchor.data.write.return_value = WriteResult(
            key="test",
            allowed=False,
            audit_id="audit_123",
            blocked_by="pii_filter",
            reason="Email detected",
        )

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        result = wrapped.add("user@example.com", user_id="user_123")

        assert result.allowed is False
        assert result.blocked_by == "pii_filter"
        assert result.reason == "Email detected"
        assert result.mem0_result is None
        mock_mem0.add.assert_not_called()

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_search(self, anchor, agent_id, mock_mem0):
        """Test searching memories."""
        from anchor.integrations.mem0 import AnchorMem0

        anchor.data.write.return_value = WriteResult(
            key="test", allowed=True, audit_id="audit_123"
        )

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        results = wrapped.search("dark mode", user_id="user_123", limit=5)

        assert len(results) == 1
        assert results[0]["id"] == "mem_123"
        mock_mem0.search.assert_called_once()
        # Should have logged the search
        anchor.data.write.assert_called_once()

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_get(self, anchor, agent_id, mock_mem0):
        """Test getting a memory by ID."""
        from anchor.integrations.mem0 import AnchorMem0

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        result = wrapped.get("mem_123")

        assert result == {"id": "mem_123", "content": "test"}
        mock_mem0.get.assert_called_once_with("mem_123")

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_get_all(self, anchor, agent_id, mock_mem0):
        """Test getting all memories."""
        from anchor.integrations.mem0 import AnchorMem0

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        results = wrapped.get_all(user_id="user_123")

        assert len(results) == 1
        mock_mem0.get_all.assert_called_once()

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_update_allowed(self, anchor, agent_id, mock_mem0):
        """Test updating memory when allowed."""
        from anchor.integrations.mem0 import AnchorMem0

        anchor.data.write.return_value = WriteResult(
            key="test", allowed=True, audit_id="audit_123"
        )

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        result = wrapped.update("mem_123", "Updated content")

        assert result.allowed is True
        mock_mem0.update.assert_called_once()

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_update_blocked(self, anchor, agent_id, mock_mem0):
        """Test updating memory when blocked."""
        from anchor.integrations.mem0 import AnchorMem0

        anchor.data.write.return_value = WriteResult(
            key="test", allowed=False, audit_id="audit_123", blocked_by="pii_filter"
        )

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        result = wrapped.update("mem_123", "user@example.com")

        assert result.allowed is False
        mock_mem0.update.assert_not_called()

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", True)
    def test_anchor_mem0_delete(self, anchor, agent_id, mock_mem0):
        """Test deleting a memory."""
        from anchor.integrations.mem0 import AnchorMem0

        wrapped = AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=mock_mem0)
        result = wrapped.delete("mem_123")

        assert result is True
        mock_mem0.delete.assert_called_once_with("mem_123")

    @patch("anchor.integrations.mem0.MEM0_AVAILABLE", False)
    def test_anchor_mem0_without_mem0(self, anchor, agent_id):
        """Test AnchorMem0 when Mem0 is not available."""
        from anchor.integrations.mem0 import AnchorMem0

        with pytest.raises(ImportError, match="Mem0 is required"):
            AnchorMem0(anchor=anchor, agent_id=agent_id, mem0_client=Mock())

class TestMCPIntegration:
    """Tests for MCP (Model Context Protocol) integration."""

    @pytest.fixture
    def anchor(self):
        """Create a mock Anchor client."""
        anchor = Mock(spec=Anchor)
        anchor.agents = Mock()
        # Mock successful agent validation
        mock_agent = Mock()
        mock_agent.id = "agent_123"
        anchor.agents.get.return_value = mock_agent
        return anchor

    @pytest.fixture
    def agent_id(self):
        """Return a test agent ID."""
        return "agent_123"

    def test_anchor_mcp_server_initialization(self, anchor, agent_id):
        """Test AnchorMCPServer initialization with validation."""
        from anchor.integrations.mcp import AnchorMCPServer

        class DummyServer:
            """Mock MCP server for testing."""
            def start(self):
                return "started"

        base_server = DummyServer()
        wrapper = AnchorMCPServer(
            anchor=anchor,
            agent_id=agent_id,
            base_server=base_server
        )

        assert wrapper.anchor == anchor
        assert wrapper.agent_id == agent_id
        assert wrapper.base_server == base_server
        # Should have validated agent exists
        anchor.agents.get.assert_called_once_with(agent_id)

    def test_anchor_mcp_server_skip_validation(self, anchor, agent_id):
        """Test AnchorMCPServer initialization without validation."""
        from anchor.integrations.mcp import AnchorMCPServer

        class DummyServer:
            """Mock MCP server for testing."""
            def start(self):
                return "started"

        wrapper = AnchorMCPServer(
            anchor=anchor,
            agent_id=agent_id,
            base_server=DummyServer(),
            validate=False
        )

        assert wrapper.agent_id == agent_id
        # Should not have called validation
        anchor.agents.get.assert_not_called()

    def test_anchor_mcp_server_validation_missing_agents_api(self, agent_id):
        """Test validation fails when anchor doesn't have agents API."""
        from anchor.integrations.mcp import AnchorMCPServer

        invalid_anchor = Mock(spec=[])

        class DummyServer:
            """Mock MCP server for testing."""
            def start(self):
                return "started"

        with pytest.raises(ValueError, match="does not expose agents API"):
            AnchorMCPServer(
                anchor=invalid_anchor,
                agent_id=agent_id,
                base_server=DummyServer()
            )

    def test_anchor_mcp_server_validation_invalid_agent_id(self, anchor):
        """Test validation fails when agent_id doesn't exist."""
        from anchor.integrations.mcp import AnchorMCPServer
        from anchor.exceptions import AnchorError

        # Mock agent.get to raise error
        anchor.agents.get.side_effect = AnchorError("Agent not found")

        class DummyServer:
            """Mock MCP server for testing."""
            def start(self):
                return "started"

        with pytest.raises(ValueError, match="Failed to validate agent_id"):
            AnchorMCPServer(
                anchor=anchor,
                agent_id="invalid_agent",
                base_server=DummyServer()
            )

    def test_anchor_mcp_server_wraps_base_server(self, anchor, agent_id):
        """Test that AnchorMCPServer delegates to base server."""
        from anchor.integrations.mcp import AnchorMCPServer

        class DummyServer:
            """Mock MCP server for testing."""
            def start(self):
                return "started"

        wrapper = AnchorMCPServer(
            anchor=anchor,
            agent_id=agent_id,
            base_server=DummyServer()
        )

        assert wrapper.start() == "started"

    def test_mcp_module_exports(self):
        """Test that MCP module exports AnchorMCPServer."""
        from anchor.integrations.mcp import AnchorMCPServer
        from anchor.integrations import mcp

        assert hasattr(mcp, "AnchorMCPServer")
        assert mcp.AnchorMCPServer is AnchorMCPServer
