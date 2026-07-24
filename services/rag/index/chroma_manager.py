"""
RAG-ALL: ChromaDB Manager
Quản lý ChromaDB vector store: create collections, add/search/delete documents.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from shared.config.settings import settings
from shared.utils.logger import rag_logger as logger


class ChromaManager:
    """
    ChromaDB wrapper cho vector storage.

    Features:
      - Persistent storage
      - Auto-create collections
      - CRUD operations
      - Search with similarity
    """

    def __init__(self):
        self._client = None
        self._collections: dict = {}

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"Connected to ChromaDB at {settings.chroma_host}:{settings.chroma_port}")
        return self._client

    def _get_collection(self, name: str):
        """Get or create a collection."""
        if name not in self._collections:
            client = self._get_client()
            self._collections[name] = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    async def add_documents(
        self,
        collection_name: str,
        doc_id: str,
        chunks: list[dict],
        embeddings: list[list[float]],
        metadata: dict = None,
    ):
        """
        Add document chunks to collection.

        Args:
            collection_name: Tên collection
            doc_id: Document ID
            chunks: List of {"text": str, "index": int, ...}
            embeddings: List of embedding vectors
            metadata: Additional metadata
        """
        collection = self._get_collection(collection_name)

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = []
        for i, chunk in enumerate(chunks):
            meta = {
                "doc_id": doc_id,
                "chunk_index": i,
                "text_length": len(chunk["text"]),
            }
            if metadata:
                meta.update(metadata)
            metadatas.append(meta)

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks to '{collection_name}' for doc {doc_id}")

    async def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search collection by embedding similarity.

        Returns list of {id, document, metadata, score}
        """
        collection = self._get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances (lower = more similar)
                # Convert to similarity score (0-1)
                distance = results["distances"][0][i] if results["distances"] else 0
                score = max(0, 1 - distance)  # Convert distance to similarity

                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": score,
                })

        return formatted

    async def list_documents(self, collection_name: str) -> list[dict]:
        """List all unique documents in collection."""
        collection = self._get_collection(collection_name)

        # Get all items
        all_items = collection.get(include=["metadatas"])

        # Group by doc_id
        doc_ids = set()
        for meta in all_items["metadatas"]:
            if meta and "doc_id" in meta:
                doc_ids.add(meta["doc_id"])

        return [{"doc_id": did} for did in doc_ids]

    async def delete_document(self, collection_name: str, doc_id: str):
        """Delete all chunks for a document."""
        collection = self._get_collection(collection_name)

        # Find all chunks for this doc
        all_items = collection.get(include=["metadatas"])
        ids_to_delete = []
        for i, meta in enumerate(all_items["metadatas"]):
            if meta and meta.get("doc_id") == doc_id:
                ids_to_delete.append(all_items["ids"][i])

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for doc {doc_id}")

    async def get_collection_stats(self, collection_name: str) -> dict:
        """Get statistics about a collection."""
        collection = self._get_collection(collection_name)
        count = collection.count()
        return {
            "collection": collection_name,
            "total_chunks": count,
        }
