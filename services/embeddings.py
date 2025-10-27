"""Embedding service using sentence-transformers with dual-embedding support."""
import logging
from typing import Optional
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using sentence-transformers with dual-embedding support."""

    def __init__(self):
        """Initialize the embedding service."""
        self._model_primary: Optional[SentenceTransformer] = None
        self._model_secondary: Optional[SentenceTransformer] = None
        logger.info(f"Embedding service initialized (models will load on first use)")
        if settings.use_dual_embeddings:
            logger.info(f"Dual-embedding mode enabled: {settings.embedding_model_primary} + {settings.embedding_model_secondary}")

    def _load_models(self):
        """Lazy load the embedding models."""
        if self._model_primary is None:
            logger.info(f"Loading primary embedding model: {settings.embedding_model_primary}")
            # Try loading from local path first (air-gapped)
            # Hugging Face cache format: models--{org}--{model}
            cache_name = f"models--sentence-transformers--{settings.embedding_model_primary.split('/')[-1]}"
            model_path = settings.models_dir / "sentence-transformers" / cache_name / "snapshots"

            # Find the snapshot directory (should be only one)
            loaded = False
            if model_path.exists():
                snapshots = list(model_path.iterdir())
                if snapshots:
                    snapshot_path = snapshots[0]
                    logger.info(f"Loading from local cache: {snapshot_path}")
                    self._model_primary = SentenceTransformer(str(snapshot_path))
                    logger.info("Primary embedding model loaded successfully")
                    loaded = True

            # Fallback: try direct path
            if not loaded:
                direct_path = settings.models_dir / "sentence-transformers" / settings.embedding_model_primary
                if direct_path.exists():
                    logger.info(f"Loading from local path: {direct_path}")
                    self._model_primary = SentenceTransformer(str(direct_path))
                    logger.info("Primary embedding model loaded successfully")
                    loaded = True

            # Fail if not found locally (air-gapped deployment)
            if not loaded:
                error_msg = (
                    f"Primary embedding model '{settings.embedding_model_primary}' not found locally. "
                    f"Expected at: {model_path} or {direct_path}. "
                    f"For air-gapped deployment, ensure models are bundled in the Docker image."
                )
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

        if settings.use_dual_embeddings and self._model_secondary is None:
            logger.info(f"Loading secondary embedding model: {settings.embedding_model_secondary}")
            # Try loading from local path first (air-gapped)
            # Hugging Face cache format: models--{org}--{model}
            cache_name = f"models--sentence-transformers--{settings.embedding_model_secondary.split('/')[-1]}"
            model_path = settings.models_dir / "sentence-transformers" / cache_name / "snapshots"

            # Find the snapshot directory (should be only one)
            loaded = False
            if model_path.exists():
                snapshots = list(model_path.iterdir())
                if snapshots:
                    snapshot_path = snapshots[0]
                    logger.info(f"Loading from local cache: {snapshot_path}")
                    self._model_secondary = SentenceTransformer(str(snapshot_path))
                    logger.info("Secondary embedding model loaded successfully")
                    loaded = True

            # Fallback: try direct path
            if not loaded:
                direct_path = settings.models_dir / "sentence-transformers" / settings.embedding_model_secondary
                if direct_path.exists():
                    logger.info(f"Loading from local path: {direct_path}")
                    self._model_secondary = SentenceTransformer(str(direct_path))
                    logger.info("Secondary embedding model loaded successfully")
                    loaded = True

            # Fail if not found locally (air-gapped deployment)
            if not loaded:
                error_msg = (
                    f"Secondary embedding model '{settings.embedding_model_secondary}' not found locally. "
                    f"Expected at: {model_path} or {direct_path}. "
                    f"For air-gapped deployment, ensure models are bundled in the Docker image."
                )
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text using primary model.

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding vector
        """
        self._load_models()

        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * settings.embedding_dimension

        try:
            # Generate embedding using primary model
            embedding = self._model_primary.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_dual_embeddings(self, text: str) -> tuple[list[float], Optional[list[float]]]:
        """
        Generate both primary and secondary embeddings for the given text.

        Args:
            text: Input text to embed

        Returns:
            Tuple of (primary_embedding, secondary_embedding)
        """
        self._load_models()

        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            zero_vec = [0.0] * settings.embedding_dimension
            return (zero_vec, zero_vec if settings.use_dual_embeddings else None)

        try:
            # Generate primary embedding
            primary_embedding = self._model_primary.encode(text, convert_to_numpy=True).tolist()

            # Generate secondary embedding if dual embeddings are enabled
            secondary_embedding = None
            if settings.use_dual_embeddings:
                secondary_embedding = self._model_secondary.encode(text, convert_to_numpy=True).tolist()

            return (primary_embedding, secondary_embedding)
        except Exception as e:
            logger.error(f"Error generating dual embeddings: {e}")
            raise

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (batch processing) using primary model.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        self._load_models()

        if not texts:
            return []

        try:
            # Batch encode for efficiency using primary model
            embeddings = self._model_primary.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def generate_batch_dual_embeddings(self, texts: list[str]) -> tuple[list[list[float]], Optional[list[list[float]]]]:
        """
        Generate both primary and secondary embeddings for multiple texts (batch processing).

        Args:
            texts: List of input texts to embed

        Returns:
            Tuple of (primary_embeddings, secondary_embeddings)
        """
        self._load_models()

        if not texts:
            return ([], [] if settings.use_dual_embeddings else None)

        try:
            # Batch encode for efficiency
            primary_embeddings = self._model_primary.encode(texts, convert_to_numpy=True).tolist()

            secondary_embeddings = None
            if settings.use_dual_embeddings:
                secondary_embeddings = self._model_secondary.encode(texts, convert_to_numpy=True).tolist()

            return (primary_embeddings, secondary_embeddings)
        except Exception as e:
            logger.error(f"Error generating batch dual embeddings: {e}")
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
