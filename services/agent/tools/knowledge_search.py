"""
RAG-ALL: Knowledge Search Tool
Tool để tìm kiếm trong knowledge base (ChromaDB).
"""

from shared.config.settings import settings
from shared.utils.logger import agent_logger as logger


class KnowledgeSearchTool:
    """Search knowledge base for relevant context."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
        return self._client

    async def search(
        self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search knowledge base.

        Args:
            query: Search query
            collection_name: Collection to search
            top_k: Number of results

        Returns:
            List of {content, score, metadata}
        """
        try:
            client = self._get_client()
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            # Get query embedding
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(settings.embedding_model)
            query_embedding = model.encode([query]).tolist()

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
            )

            formatted = []
            if results and results.get("documents"):
                docs = results["documents"][0]
                distances = results.get("distances", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]

                for i, doc in enumerate(docs):
                    formatted.append({
                        "content": doc,
                        "score": 1 - distances[i] if i < len(distances) else 0,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                    })

            logger.info(f"KB search: {len(formatted)} results for '{query[:30]}...'")
            return formatted

        except Exception as e:
            logger.error(f"KB search error: {e}")
            return []
