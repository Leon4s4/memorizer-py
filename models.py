"""Data models for Memorizer."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class RelationshipType(str, Enum):
    """Types of relationships between memories."""
    RELATED_TO = "related-to"
    EXAMPLE_OF = "example-of"
    EXPLAINS = "explains"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends-on"
    SUPERSEDES = "supersedes"


class MemoryRelationship(BaseModel):
    """Relationship between two memories."""
    id: UUID = Field(default_factory=uuid4)
    from_memory_id: UUID
    to_memory_id: UUID
    type: RelationshipType
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Memory(BaseModel):
    """Memory entity with embeddings and metadata."""
    id: UUID = Field(default_factory=uuid4)
    type: str
    content: dict[str, Any]
    text: Optional[str] = None
    source: str
    tags: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Embeddings (not stored in model, managed by vector DB)
    embedding: Optional[list[float]] = None
    embedding_metadata: Optional[list[float]] = None

    # Similarity score (only present in search results)
    similarity: Optional[float] = None

    # Related memories (populated on demand)
    relationships: list[MemoryRelationship] = Field(default_factory=list)


class MemoryCreate(BaseModel):
    """Request to create a new memory."""
    type: str
    content: dict[str, Any]
    source: str
    tags: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    title: Optional[str] = None
    relationships: list[dict[str, Any]] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    """Request to update a memory."""
    type: Optional[str] = None
    content: Optional[dict[str, Any]] = None
    source: Optional[str] = None
    tags: Optional[list[str]] = None
    confidence: Optional[float] = None
    title: Optional[str] = None


class MemorySearchRequest(BaseModel):
    """Request to search memories."""
    query: str
    limit: int = 10
    tags: list[str] = Field(default_factory=list)
    include_relationships: bool = False


class MemorySearchResponse(BaseModel):
    """Response from memory search."""
    memories: list[Memory]
    total: int
    query: str


class RelationshipCreate(BaseModel):
    """Request to create a relationship."""
    from_memory_id: UUID
    to_memory_id: UUID
    type: RelationshipType


class MemoryStats(BaseModel):
    """Statistics about the memory system."""
    total_memories: int
    memories_with_titles: int
    memories_without_titles: int
    total_relationships: int
    unique_tags: int
    unique_types: int
    avg_confidence: float
    oldest_memory: Optional[datetime] = None
    newest_memory: Optional[datetime] = None
