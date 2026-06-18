"""Chroma-backed vector memory store for semantic code library retrieval."""

import hashlib

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from smart_code_lib.llm.local_models import DEFAULT_EMBEDDING_MODEL, get_embeddings


class VectorMemoryStore:
    """Persistent vector store using Chroma and local HuggingFace embeddings."""

    def __init__(self, persist_directory: str = "./.chroma_db"):
        """Initialize the vector store with local embeddings and Chroma persistence."""
        self.embedding_model = DEFAULT_EMBEDDING_MODEL
        self.embeddings = get_embeddings()
        self.db = Chroma(
            collection_name="smart_library_core",
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

    def insert_reference(self, content: str, category: str, language: str = "All") -> None:
        """Insert a reference document into the vector store."""
        doc = Document(
            page_content=content,
            metadata={"category": category, "language": language},
        )
        self.db.add_documents([doc])

    def query_context(self, query: str, limit: int = 3) -> str:
        """Return formatted context strings from the top-k similar documents."""
        results = self.db.similarity_search(query, k=limit)
        return "\n\n".join(
            [f"[{r.metadata.get('category')}]: {r.page_content}" for r in results]
        )

    def list_documents(self, limit: int = 1000) -> list:
        """Return documents with id, content, and metadata from the collection."""
        result = self.db._collection.get(
            limit=limit,
            include=["documents", "metadatas"],
        )
        ids = result.get("ids") or []
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        return [
            {
                "id": doc_id,
                "content": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
            }
            for i, doc_id in enumerate(ids)
        ]

    def deduplicate(
        self, similarity_threshold: float = 0.95, dry_run: bool = True
    ) -> dict:
        """
        Remove exact and near-duplicate documents from the vector store.

        Exact duplicates are detected via content hash. Near-duplicates use
        cosine similarity on stored embeddings. The first/oldest document in
        collection order is kept; later matches are removed.
        """
        collection = self.db._collection
        result = collection.get(include=["documents", "metadatas", "embeddings"])

        ids = result.get("ids") or []
        if not ids:
            return {"removed": 0, "kept": 0, "dry_run": dry_run}

        documents = result.get("documents") or []
        embeddings = result.get("embeddings") or []

        kept_hashes: set[str] = set()
        kept_embeddings: list[list[float]] = []
        remove_ids: list[str] = []

        for i, doc_id in enumerate(ids):
            content = documents[i] if i < len(documents) else ""
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            embedding = embeddings[i] if i < len(embeddings) else None

            is_duplicate = content_hash in kept_hashes
            if not is_duplicate and embedding is not None:
                for kept_embedding in kept_embeddings:
                    if _cosine_similarity(embedding, kept_embedding) >= similarity_threshold:
                        is_duplicate = True
                        break

            if is_duplicate:
                remove_ids.append(doc_id)
            else:
                kept_hashes.add(content_hash)
                if embedding is not None:
                    kept_embeddings.append(embedding)

        if not dry_run and remove_ids:
            collection.delete(ids=remove_ids)

        kept_count = len(ids) - len(remove_ids)
        return {"removed": len(remove_ids), "kept": kept_count, "dry_run": dry_run}


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)