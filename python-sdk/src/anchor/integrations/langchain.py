"""
Anchor LangChain Integration.

Policy-checked memory, audit logging, and checkpoint/rollback for LangChain agents.

Components:
- AnchorMemory: LangChain memory with policy enforcement and checkpoints
- AnchorChatHistory: Drop-in replacement for chat history with policy checks
- AnchorCallbackHandler: Audit logging for chain operations

Usage:
    from anchor import Anchor
    from anchor.integrations.langchain import AnchorMemory, AnchorCallbackHandler
    from langchain.agents import AgentExecutor

    anchor = Anchor(api_key="your-api-key")
    agent = anchor.agents.create(name="langchain-agent")

    # Configure policies
    anchor.config.update(agent.id, {
        "policies": {"block_pii": True, "retention_days": 30}
    })

    # Create memory (uses anchor.data for storage)
    memory = AnchorMemory(anchor=anchor, agent_id=agent.id)

    # Create callback handler (logs to anchor.audit)
    callbacks = AnchorCallbackHandler(anchor=anchor, agent_id=agent.id)

    # Use with LangChain
    executor = AgentExecutor(agent=lc_agent, tools=tools, memory=memory)
    result =executor.invoke({"input": "Hello"}, config={"callbacks": [callbacks]})

    # Checkpoint & audit
    checkpoint_id = memory.create_checkpoint(label="before-experiment")
    events = anchor.audit.query(agent.id, limit=50)
    verification = anchor.audit.verify(agent.id)  # Verify chain integrity
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

try:
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
    )

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseChatMessageHistory = object
    BaseMessage = object
    HumanMessage = object
    AIMessage = object
    SystemMessage = object


class AnchorMemory:
    """
    LangChain memory with policy enforcement, persistent storage, and checkpoints.

    Description: Stores conversation history using anchor.data with:
    - Policy enforcement (PII blocking, etc.)
    - Automatic audit logging
    - Checkpoint/rollback support

    Usage:
        from anchor import Anchor
        from anchor.integrations.langchain import AnchorMemory

        anchor = Anchor(api_key="your-api-key")
        agent = anchor.agents.create("my-agent")

        memory = AnchorMemory(anchor=anchor, agent_id=agent.id)

        # Use with LangChain
        chain = ConversationChain(llm=llm, memory=memory)
        checkpoint_id = memory.create_checkpoint(label="before-experiment")
    """

    def __init__(
        self,
        anchor: Any,
        agent_id: str,
        memory_key: str = "chat_history",
        return_messages: bool = True,
        session_id: Optional[str] = None,
    ):
        """
        Initialize AnchorMemory.

        Args:
            anchor: Anchor client instance
            agent_id: Agent identifier
            memory_key: Key to use in chain context
            return_messages: Return as messages (True) or string (False)
            session_id: Optional session ID for grouping messages
        """
        self.anchor = anchor
        self.agent_id = agent_id
        self.memory_key = memory_key
        self.return_messages = return_messages
        self.session_id = session_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._messages: List[Any] = []

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variable names."""
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory for chain context."""
        # Load from Anchor data store
        self._load_from_anchor()

        if self.return_messages:
            return {self.memory_key: self._messages}
        else:
            return {self.memory_key: self._messages_to_string()}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation turn to Anchor (persistent storage, survives restarts)."""
        input_str = inputs.get("input", "")
        output_str = outputs.get("output", "")

        timestamp = datetime.now(timezone.utc).isoformat()

        if input_str:
            if LANGCHAIN_AVAILABLE:
                self._messages.append(HumanMessage(content=input_str))
            # Store in Anchor (policy-checked)
            self.anchor.data.write(
                self.agent_id,
                f"chat:{self.session_id}:human:{timestamp}",
                input_str,
                metadata={"role": "human", "session_id": self.session_id},
            )

        if output_str:
            if LANGCHAIN_AVAILABLE:
                self._messages.append(AIMessage(content=output_str))
            # Store in Anchor (policy-checked)
            self.anchor.data.write(
                self.agent_id,
                f"chat:{self.session_id}:ai:{timestamp}",
                output_str,
                metadata={"role": "ai", "session_id": self.session_id},
            )

    def clear(self) -> None:
        """Clear conversation history."""
        self._messages = []
        # Delete from Anchor
        self.anchor.data.delete_prefix(self.agent_id, f"chat:{self.session_id}:")

    def _load_from_anchor(self) -> None:
        """Load messages from Anchor (includes historical data from previous sessions)."""
        if not LANGCHAIN_AVAILABLE:
            return

        # List keys for this session
        keys = self.anchor.data.list(self.agent_id, prefix=f"chat:{self.session_id}:")

        self._messages = []
        for key in sorted(keys):
            entry = self.anchor.data.read_full(self.agent_id, key)
            if entry:
                role = (
                    entry.metadata.get("role", "human") if entry.metadata else "human"
                )
                if role == "human":
                    self._messages.append(HumanMessage(content=entry.value))
                elif role == "ai":
                    self._messages.append(AIMessage(content=entry.value))
                elif role == "system":
                    self._messages.append(SystemMessage(content=entry.value))

    def _messages_to_string(self) -> str:
        """Convert messages to string format."""
        lines = []
        for msg in self._messages:
            if LANGCHAIN_AVAILABLE:
                if isinstance(msg, HumanMessage):
                    lines.append(f"Human: {msg.content}")
                elif isinstance(msg, AIMessage):
                    lines.append(f"AI: {msg.content}")
                elif isinstance(msg, SystemMessage):
                    lines.append(f"System: {msg.content}")
        return "\n".join(lines)

    def create_checkpoint(self, label: Optional[str] = None) -> str:
        """
        Create a checkpoint of current conversation state.

        Args:
            label: Optional label for the checkpoint

        Returns:
            Checkpoint ID

        Example:
            # Create checkpoint before risky operation
            checkpoint_id = memory.create_checkpoint(label="before-migration")
            
            # ... perform risky operations ...
            
            # If corruption detected, restore
            memory.restore_checkpoint(checkpoint_id)
        """
        checkpoint = self.anchor.checkpoints.create(
            self.agent_id, label=label or f"langchain-{self.session_id}"
        )
        return checkpoint.id

    def restore_checkpoint(self, checkpoint_id: str) -> None:
        """
        Restore conversation to a previous checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore

        Example:
            # Restore to checkpoint after detecting corruption
            memory.restore_checkpoint(checkpoint_id)
            print("Conversation restored to checkpoint")
        """
        self.anchor.checkpoints.restore(self.agent_id, checkpoint_id)
        self._messages = []
        self._load_from_anchor()


class AnchorChatHistory(BaseChatMessageHistory if LANGCHAIN_AVAILABLE else object):
    """
    LangChain ChatMessageHistory backed by Anchor.

    Description: Drop-in replacement for LangChain's chat history that stores
    messages in Anchor's policy-checked data store.

    Usage:
        from anchor import Anchor
        from anchor.integrations.langchain import AnchorChatHistory

        anchor = Anchor(api_key="your-api-key")
        agent = anchor.agents.create("chat-agent")

        history = AnchorChatHistory(anchor=anchor, agent_id=agent.id)

        # Use with RunnableWithMessageHistory
        with_history = RunnableWithMessageHistory(
            chain,
            lambda session_id: history,
            input_messages_key="input",
            history_messages_key="history"
        )
    """

    def __init__(self, anchor: Any, agent_id: str, session_id: Optional[str] = None):
        """
        Initialize AnchorChatHistory.

        Args:
            anchor: Anchor client instance
            agent_id: Agent identifier
            session_id: Optional session ID
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required. Install with: pip install langchain-core"
            )

        self.anchor = anchor
        self.agent_id = agent_id
        self.session_id = session_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve all messages."""
        keys = self.anchor.data.list(self.agent_id, prefix=f"chat:{self.session_id}:")

        messages = []
        for key in sorted(keys):
            entry = self.anchor.data.read_full(self.agent_id, key)
            if entry:
                role = (
                    entry.metadata.get("role", "human") if entry.metadata else "human"
                )
                if role == "human":
                    messages.append(HumanMessage(content=entry.value))
                elif role == "ai":
                    messages.append(AIMessage(content=entry.value))
                elif role == "system":
                    messages.append(SystemMessage(content=entry.value))

        return messages

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to history."""
        timestamp = datetime.now(timezone.utc).isoformat()

        if isinstance(message, HumanMessage):
            role = "human"
        elif isinstance(message, AIMessage):
            role = "ai"
        elif isinstance(message, SystemMessage):
            role = "system"
        else:
            role = "human"

        content = (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )

        self.anchor.data.write(
            self.agent_id,
            f"chat:{self.session_id}:{role}:{timestamp}",
            content,
            metadata={"role": role, "session_id": self.session_id},
        )

    def clear(self) -> None:
        """Clear all messages."""
        self.anchor.data.delete_prefix(self.agent_id, f"chat:{self.session_id}:")


class AnchorCallbackHandler:
    """
    LangChain callback handler for audit logging.

    Description: Logs chain operations to Anchor's audit trail (hash-chained, verifiable).

    Usage:
        from anchor import Anchor
        from anchor.integrations.langchain import AnchorCallbackHandler

        anchor = Anchor(api_key="your-api-key")
        handler = AnchorCallbackHandler(anchor=anchor, agent_id="agent_123")

        # Use with chain
        result = chain.invoke(input, config={"callbacks": [handler]})

        # Query audit logs
        events = anchor.audit.query(agent_id="agent_123")
        verification = anchor.audit.verify(agent_id="agent_123")
    """

    def __init__(
        self,
        anchor: Any,
        agent_id: str,
        log_prompts: bool = True,
        log_completions: bool = True,
        log_tool_calls: bool = True,
    ):
        """
        Initialize callback handler.

        Args:
            anchor: Anchor client instance
            agent_id: Agent identifier
            log_prompts: Log input prompts
            log_completions: Log completions
            log_tool_calls: Log tool invocations
        """
        self.anchor = anchor
        self.agent_id = agent_id
        self.log_prompts = log_prompts
        self.log_completions = log_completions
        self.log_tool_calls = log_tool_calls

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs
    ) -> None:
        """Called when LLM starts. Logs to audit trail (automatically hash-chained)."""
        if self.log_prompts:
            # Log to audit (operations are automatically logged to hash-chained audit trail)
            for i, prompt in enumerate(prompts):
                self.anchor.data.write(
                    self.agent_id,
                    f"llm:prompt:{datetime.now(timezone.utc).isoformat()}:{i}",
                    prompt[:1000],  # Truncate for storage
                    metadata={"type": "llm_prompt"},
                )

    def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM completes. Logs to audit trail (automatically hash-chained)."""
        if self.log_completions:
            # Log completion (automatically added to hash-chained audit trail)
            output = str(response)[:1000] if response else ""
            self.anchor.data.write(
                self.agent_id,
                f"llm:completion:{datetime.now(timezone.utc).isoformat()}",
                output,
                metadata={"type": "llm_completion"},
            )

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs
    ) -> None:
        """Called when tool starts. Logs to audit trail (automatically hash-chained)."""
        if self.log_tool_calls:
            tool_name = serialized.get("name", "unknown")
            self.anchor.data.write(
                self.agent_id,
                f"tool:start:{tool_name}:{datetime.now(timezone.utc).isoformat()}",
                input_str[:500],
                metadata={"type": "tool_start", "tool": tool_name},
            )

    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when tool completes. Logs to audit trail (automatically hash-chained)."""
        if self.log_tool_calls:
            self.anchor.data.write(
                self.agent_id,
                f"tool:end:{datetime.now(timezone.utc).isoformat()}",
                output[:500] if output else "",
                metadata={"type": "tool_end"},
            )
