"""Embedding service using sentence-transformers."""
import logging
from typing import Optional
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using sentence-transformers."""

    def __init__(self):
        """Initialize the embedding service."""
        self._model: Optional[SentenceTransformer] = None
        logger.info(f"Embedding service initialized (model will load on first use)")

    def _load_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded successfully")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding vector
        """
        self._load_model()

        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * settings.embedding_dimension

        try:
            # Generate embedding
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (batch processing).

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        self._load_model()

        if not texts:
            return []

        try:
            # Batch encode for efficiency
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return settings.embedding_dimension


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
