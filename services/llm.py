"""LLM service using llama-cpp-python."""
import logging
from typing import Optional
from pathlib import Path
from llama_cpp import Llama
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM operations using llama-cpp-python."""

    def __init__(self):
        """Initialize the LLM service."""
        self._model: Optional[Llama] = None
        self._model_loaded = False
        logger.info("LLM service initialized (model will load on first use)")

    def _load_model(self):
        """Lazy load the LLM model."""
        if self._model is not None:
            return

        model_path = Path(settings.llm_model_path)

        if not model_path.exists():
            logger.warning(f"LLM model not found at {model_path}")
            logger.warning("Title generation will be disabled")
            logger.warning("To enable: Download a GGUF model and place it at the configured path")
            self._model_loaded = False
            return

        try:
            logger.info(f"Loading LLM model from: {model_path}")
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=settings.llm_context_size,
                n_threads=4,
                n_gpu_layers=0,  # Set to -1 to use GPU if available
                verbose=False
            )
            self._model_loaded = True
            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading LLM model: {e}")
            logger.warning("Title generation will be disabled")
            self._model_loaded = False

    def is_available(self) -> bool:
        """Check if the LLM is available."""
        if not self._model_loaded:
            self._load_model()
        return self._model_loaded

    def generate_title(self, content: str, max_length: int = 100) -> Optional[str]:
        """
        Generate a title for the given content.

        Args:
            content: The content to generate a title for
            max_length: Maximum length of the content to process

        Returns:
            Generated title or None if LLM is not available
        """
        if not self.is_available():
            return None

        # Truncate content if too long
        content_preview = content[:max_length] if len(content) > max_length else content

        prompt = f"""Generate a short, descriptive title (max 10 words) for this content:

{content_preview}

Title:"""

        try:
            response = self._model(
                prompt,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                stop=["\n", "Title:", "Content:"],
                echo=False
            )

            title = response['choices'][0]['text'].strip()

            # Clean up the title
            title = title.replace('"', '').replace("'", "").strip()

            # Limit to 10 words
            words = title.split()
            if len(words) > 10:
                title = ' '.join(words[:10])

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return None

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None if LLM is not available
        """
        if not self.is_available():
            return None

        try:
            response = self._model(
                prompt,
                max_tokens=max_tokens or settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                echo=False
            )

            return response['choices'][0]['text'].strip()

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None


# Global singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
