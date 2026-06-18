"""Tests for vector_store cosine similarity and deduplication logic."""

from unittest.mock import MagicMock, patch

import pytest

from smart_code_lib.database.vector_store import VectorMemoryStore, _cosine_similarity


def test_cosine_similarity_identical_vectors():
    """Identical unit vectors have similarity 1.0."""
    vec = [1.0, 0.0, 0.0]
    assert _cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    """Orthogonal vectors have similarity 0.0."""
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    """Zero-norm vectors return 0.0 to avoid division by zero."""
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_cosine_similarity_partial_overlap():
    """Similar but not identical vectors score between 0 and 1."""
    score = _cosine_similarity([1.0, 1.0], [1.0, 0.0])
    assert 0.0 < score < 1.0


def _make_store_with_collection(collection):
    """Build VectorMemoryStore with mocked Chroma collection."""
    with (
        patch("smart_code_lib.database.vector_store.get_embeddings"),
        patch("smart_code_lib.database.vector_store.Chroma") as mock_chroma,
    ):
        mock_chroma.return_value._collection = collection
        store = VectorMemoryStore(persist_directory="./test_chroma")
    store.db._collection = collection
    return store


def test_deduplicate_empty_collection():
    """Empty collection returns zero removed/kept."""
    collection = MagicMock()
    collection.get.return_value = {"ids": []}
    store = _make_store_with_collection(collection)

    result = store.deduplicate(dry_run=True)

    assert result == {"removed": 0, "kept": 0, "dry_run": True}
    collection.delete.assert_not_called()


def test_deduplicate_exact_content_hash():
    """Exact duplicate content is marked for removal (keeps first)."""
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["id-1", "id-2"],
        "documents": ["same text", "same text"],
        "embeddings": [[1.0, 0.0], [0.0, 1.0]],
    }
    store = _make_store_with_collection(collection)

    result = store.deduplicate(similarity_threshold=0.95, dry_run=True)

    assert result == {"removed": 1, "kept": 1, "dry_run": True}
    collection.delete.assert_not_called()


def test_deduplicate_near_duplicate_by_embedding():
    """Near-duplicate embeddings above threshold are removed."""
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["id-1", "id-2"],
        "documents": ["doc a", "doc a variant"],
        "embeddings": [[1.0, 0.0], [0.99, 0.01]],
    }
    store = _make_store_with_collection(collection)

    result = store.deduplicate(similarity_threshold=0.95, dry_run=True)

    assert result["removed"] == 1
    assert result["kept"] == 1


def test_deduplicate_dry_run_does_not_delete():
    """dry_run=True previews removals without calling delete."""
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["id-1", "id-2"],
        "documents": ["dup", "dup"],
        "embeddings": [[1.0, 0.0], [1.0, 0.0]],
    }
    store = _make_store_with_collection(collection)

    store.deduplicate(dry_run=True)

    collection.delete.assert_not_called()


def test_deduplicate_applies_delete_when_not_dry_run():
    """dry_run=False deletes duplicate ids."""
    collection = MagicMock()
    collection.get.return_value = {
        "ids": ["id-1", "id-2"],
        "documents": ["dup", "dup"],
        "embeddings": [[1.0, 0.0], [1.0, 0.0]],
    }
    store = _make_store_with_collection(collection)

    result = store.deduplicate(dry_run=False)

    assert result["removed"] == 1
    collection.delete.assert_called_once_with(ids=["id-2"])