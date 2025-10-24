"""Storage service using ChromaDB."""
import logging
import json
from datetime import datetime
from typing import Optional
from uuid import UUID
import chromadb
from chromadb.config import Settings as ChromaSettings
from models import Memory, MemoryRelationship, RelationshipType, MemoryStats
from services.embeddings import get_embedding_service
from config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for memory storage using ChromaDB."""

    def __init__(self):
        """Initialize the storage service."""
        logger.info(f"Initializing ChromaDB at: {settings.chroma_dir}")

        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collections
        self._memories_collection = self._client.get_or_create_collection(
            name="memories",
            metadata={"description": "Memory storage with full content embeddings"}
        )

        self._metadata_collection = self._client.get_or_create_collection(
            name="memories_metadata",
            metadata={"description": "Memory storage with metadata-only embeddings"}
        )

        # In-memory storage for relationships (could be persisted to JSON file)
        self._relationships: dict[str, MemoryRelationship] = {}

        self._embedding_service = get_embedding_service()

        logger.info("Storage service initialized")

    def _extract_text(self, content: dict) -> str:
        """Extract text content from JSON."""
        # Simple text extraction - customize based on your content structure
        if isinstance(content, dict):
            return json.dumps(content, indent=2)
        return str(content)

    def _create_metadata_text(self, memory: Memory) -> str:
        """Create metadata-only text for embedding."""
        parts = []
        if memory.title:
            parts.append(f"Title: {memory.title}")
        if memory.tags:
            parts.append(f"Tags: {', '.join(memory.tags)}")
        parts.append(f"Type: {memory.type}")
        parts.append(f"Source: {memory.source}")
        return "\n".join(parts)

    def create(self, memory: Memory) -> Memory:
        """
        Create a new memory with embeddings.

        Args:
            memory: Memory to create

        Returns:
            Created memory with embeddings
        """
        logger.info(f"Creating memory: {memory.id}")

        # Extract text content
        text_content = self._extract_text(memory.content)
        memory.text = text_content

        # Generate full content embedding
        full_embedding = self._embedding_service.generate_embedding(text_content)

        # Generate metadata embedding
        metadata_text = self._create_metadata_text(memory)
        metadata_embedding = self._embedding_service.generate_embedding(metadata_text)

        # Store in ChromaDB
        memory_dict = memory.model_dump(exclude={'embedding', 'embedding_metadata', 'similarity', 'relationships'})
        memory_dict['created_at'] = memory.created_at.isoformat()
        memory_dict['updated_at'] = memory.updated_at.isoformat()
        memory_dict['id'] = str(memory.id)

        # Add to full content collection
        self._memories_collection.add(
            ids=[str(memory.id)],
            embeddings=[full_embedding],
            metadatas=[memory_dict],
            documents=[text_content]
        )

        # Add to metadata collection
        self._metadata_collection.add(
            ids=[str(memory.id)],
            embeddings=[metadata_embedding],
            metadatas=[memory_dict],
            documents=[metadata_text]
        )

        logger.info(f"Memory created successfully: {memory.id}")
        return memory

    def get(self, memory_id: UUID) -> Optional[Memory]:
        """
        Get a memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory or None if not found
        """
        try:
            result = self._memories_collection.get(
                ids=[str(memory_id)],
                include=["metadatas", "documents"]
            )

            if not result['ids']:
                return None

            metadata = result['metadatas'][0]
            metadata['id'] = UUID(metadata['id'])
            metadata['created_at'] = datetime.fromisoformat(metadata['created_at'])
            metadata['updated_at'] = datetime.fromisoformat(metadata['updated_at'])

            memory = Memory(**metadata)

            # Load relationships
            memory.relationships = self.get_relationships(memory_id)

            return memory

        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None

    def update(self, memory_id: UUID, updates: dict) -> Optional[Memory]:
        """
        Update a memory.

        Args:
            memory_id: Memory ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated memory or None if not found
        """
        memory = self.get(memory_id)
        if not memory:
            return None

        # Apply updates
        for key, value in updates.items():
            if value is not None and hasattr(memory, key):
                setattr(memory, key, value)

        memory.updated_at = datetime.utcnow()

        # Delete old versions
        self.delete(memory_id)

        # Recreate with updated data
        return self.create(memory)

    def delete(self, memory_id: UUID) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            self._memories_collection.delete(ids=[str(memory_id)])
            self._metadata_collection.delete(ids=[str(memory_id)])

            # Delete associated relationships
            to_delete = [
                rel_id for rel_id, rel in self._relationships.items()
                if rel.from_memory_id == memory_id or rel.to_memory_id == memory_id
            ]
            for rel_id in to_delete:
                del self._relationships[rel_id]

            logger.info(f"Memory deleted: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 10,
        tags: Optional[list[str]] = None,
        use_fallback: bool = True
    ) -> list[Memory]:
        """
        Search memories using semantic similarity.

        Args:
            query: Search query
            limit: Maximum number of results
            tags: Optional tag filter
            use_fallback: Whether to use fallback threshold if no results

        Returns:
            List of matching memories with similarity scores
        """
        logger.info(f"Searching memories: query='{query}', limit={limit}, tags={tags}")

        # Generate query embedding
        query_embedding = self._embedding_service.generate_embedding(query)

        # Search in both collections
        full_results = self._memories_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit * 2,  # Get more results to filter
            include=["metadatas", "documents", "distances"]
        )

        metadata_results = self._metadata_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit * 2,
            include=["metadatas", "documents", "distances"]
        )

        # Combine and score results
        combined_scores = {}

        # Process full content results
        for idx, memory_id in enumerate(full_results['ids'][0]):
            # Convert distance to similarity (1 - distance for L2)
            similarity = 1.0 - full_results['distances'][0][idx]
            combined_scores[memory_id] = {'full': similarity, 'metadata': 0.0}

        # Process metadata results
        for idx, memory_id in enumerate(metadata_results['ids'][0]):
            similarity = 1.0 - metadata_results['distances'][0][idx]
            if memory_id in combined_scores:
                combined_scores[memory_id]['metadata'] = similarity
            else:
                combined_scores[memory_id] = {'full': 0.0, 'metadata': similarity}

        # Calculate final scores (average of both)
        final_scores = []
        for memory_id, scores in combined_scores.items():
            avg_similarity = (scores['full'] + scores['metadata']) / 2.0

            # Tag boosting
            metadata = next(
                (m for i, m in enumerate(full_results['metadatas'][0])
                 if full_results['ids'][0][i] == memory_id),
                None
            )

            if metadata and tags:
                memory_tags = metadata.get('tags', [])
                if any(tag in memory_tags for tag in tags):
                    avg_similarity += settings.tag_boost

            final_scores.append((memory_id, avg_similarity, metadata))

        # Sort by similarity
        final_scores.sort(key=lambda x: x[1], reverse=True)

        # Apply threshold
        threshold = settings.similarity_threshold
        filtered_scores = [s for s in final_scores if s[1] >= threshold]

        # Fallback if no results
        if not filtered_scores and use_fallback:
            logger.info("No results with standard threshold, trying fallback")
            threshold = settings.fallback_threshold
            filtered_scores = [s for s in final_scores if s[1] >= threshold]

        # Limit results
        filtered_scores = filtered_scores[:limit]

        # Convert to Memory objects
        memories = []
        for memory_id, similarity, metadata in filtered_scores:
            if metadata:
                metadata['id'] = UUID(metadata['id'])
                metadata['created_at'] = datetime.fromisoformat(metadata['created_at'])
                metadata['updated_at'] = datetime.fromisoformat(metadata['updated_at'])
                memory = Memory(**metadata)
                memory.similarity = similarity
                memories.append(memory)

        logger.info(f"Found {len(memories)} memories")
        return memories

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Memory]:
        """
        List all memories with pagination.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of memories
        """
        # Get all memory IDs
        result = self._memories_collection.get(
            include=["metadatas"],
            limit=limit,
            offset=offset
        )

        memories = []
        for idx, memory_id in enumerate(result['ids']):
            metadata = result['metadatas'][idx]
            metadata['id'] = UUID(metadata['id'])
            metadata['created_at'] = datetime.fromisoformat(metadata['created_at'])
            metadata['updated_at'] = datetime.fromisoformat(metadata['updated_at'])
            memories.append(Memory(**metadata))

        return memories

    def create_relationship(self, relationship: MemoryRelationship) -> MemoryRelationship:
        """Create a relationship between memories."""
        self._relationships[str(relationship.id)] = relationship
        logger.info(f"Relationship created: {relationship.from_memory_id} -> {relationship.to_memory_id}")
        return relationship

    def get_relationships(self, memory_id: UUID) -> list[MemoryRelationship]:
        """Get all relationships for a memory."""
        return [
            rel for rel in self._relationships.values()
            if rel.from_memory_id == memory_id or rel.to_memory_id == memory_id
        ]

    def delete_relationship(self, relationship_id: UUID) -> bool:
        """Delete a relationship."""
        if str(relationship_id) in self._relationships:
            del self._relationships[str(relationship_id)]
            return True
        return False

    def get_stats(self) -> MemoryStats:
        """Get statistics about the memory system."""
        all_memories = self.list_all(limit=10000)

        total = len(all_memories)
        with_titles = sum(1 for m in all_memories if m.title)
        without_titles = total - with_titles

        all_tags = set()
        all_types = set()
        confidences = []
        dates = []

        for memory in all_memories:
            all_tags.update(memory.tags)
            all_types.add(memory.type)
            confidences.append(memory.confidence)
            dates.append(memory.created_at)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return MemoryStats(
            total_memories=total,
            memories_with_titles=with_titles,
            memories_without_titles=without_titles,
            total_relationships=len(self._relationships),
            unique_tags=len(all_tags),
            unique_types=len(all_types),
            avg_confidence=avg_confidence,
            oldest_memory=min(dates) if dates else None,
            newest_memory=max(dates) if dates else None
        )


# Global singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create the global storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
