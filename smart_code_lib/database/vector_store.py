"""Chroma-backed vector memory store for semantic code library retrieval."""

import os

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


class VectorMemoryStore:
    """Persistent vector store using Chroma and OpenAI embeddings."""

    def __init__(self, persist_directory: str = "./.chroma_db"):
        """
        Initialize the vector store with OpenAI embeddings and Chroma persistence.

        Raises:
            ValueError: If OPENAI_API_KEY is missing from the environment.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required but not set. "
                "Add it to your .env file or export it before starting the API."
            )

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )
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