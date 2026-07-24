"""
RAG-ALL: Embedding Manager
Quản lý sentence-transformers embeddings cho RAG pipeline.

Models:
  - all-MiniLM-L6-v2: Default, fast, good quality
  - bge-m3: Multilingual, better for Vietnamese
"""

import numpy as np
from shared.config.settings import settings
from shared.utils.logger import rag_logger as logger


class EmbeddingManager:
    """
    Sentence-Transformers embedding wrapper.

    Generates embeddings for text chunks and queries.
    Supports batch encoding for efficiency.
    """

    def __init__(self):
        self._model = None
        self._model_name = settings.embedding_model

    def _ensure_model(self):
        """Lazy load model on first use."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            logger.info(f"Model loaded: {self._model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode texts into embedding vectors.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        self._ensure_model()

        if not texts:
            return []

        # Batch encode
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        # Convert to list of lists
        return embeddings.tolist()

    def encode_single(self, text: str) -> list[float]:
        """Encode a single text."""
        return self.encode([text])[0]

    def similarity(self, emb1: list[float], emb2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
