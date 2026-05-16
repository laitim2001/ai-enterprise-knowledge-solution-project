"""C10 §7 Conversation persistence — Tier 1 server-side per ADR-0031 Option B.

Re-exports the `ConversationStore` Protocol + the `make_conversation_store`
factory so call sites import a single name (mirrors `kb_management` barrel).
"""

from conversations.store import (
    ConversationNotFoundError,
    ConversationStore,
    InMemoryConversationStore,
    make_conversation_store,
)

__all__ = [
    "ConversationNotFoundError",
    "ConversationStore",
    "InMemoryConversationStore",
    "make_conversation_store",
]
