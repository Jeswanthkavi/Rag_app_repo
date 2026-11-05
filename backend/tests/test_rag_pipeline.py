import asyncio
import pytest
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.extractor import DocumentExtractor, PageBlock
from app.rag.chunker import SemanticChunker
from app.rag.embeddings import EmbeddingGenerator
from app.rag.synthesizer import RAGSynthesizer, Citation


@pytest.mark.asyncio
async def test_extractor_plaintext():
    sample_text = "This is a test document.\nIt contains multiple lines.\nPage 1 content."
    blocks = DocumentExtractor.extract(sample_text.encode("utf-8"), mime_type="text/plain")
    assert len(blocks) >= 1
    assert blocks[0].page_number == 1
    assert "test document" in blocks[0].text


def test_chunker_preserves_page_numbers():
    chunker = SemanticChunker(target_chunk_tokens=50, chunk_overlap_tokens=10)
    pages = [
        PageBlock(
            page_number=1,
            text="Antigravity architecture delivers high performance RAG. It organizes vector indexes with HNSW.",
        ),
        PageBlock(
            page_number=2,
            text="Second page covers multi-tenancy. Row Level Security ensures strict data isolation for every user.",
        ),
    ]
    chunks = chunker.chunk_document(pages, document_id="doc-123", document_name="Manual.pdf")

    assert len(chunks) >= 2
    # Check that metadata has document_name and correct page_number
    page_nums = {c.page_number for c in chunks}
    assert 1 in page_nums
    assert 2 in page_nums
    for c in chunks:
        assert c.metadata["document_name"] == "Manual.pdf"
        assert c.metadata["document_id"] == "doc-123"
        assert c.chunk_index is not None


@pytest.mark.asyncio
async def test_embedding_generator_dimension():
    embedder = EmbeddingGenerator(dimension=768)
    texts = [
        "First passage about database migrations and pgvector.",
        "Second passage regarding FastAPI streaming SSE responses.",
    ]
    embeddings = await embedder.generate_embeddings(texts)

    assert len(embeddings) == 2
    for emb in embeddings:
        assert len(emb) == 768, f"Expected 768 dimensions, got {len(emb)}"


@pytest.mark.asyncio
async def test_synthesizer_strict_citation():
    synthesizer = RAGSynthesizer()

    retrieved_chunks = [
        {
            "id": "c1",
            "document_id": "d1",
            "document_name": "QuarterlyReport.pdf",
            "page_number": 3,
            "content": "In Q3, enterprise revenue increased by 42% reaching $12.5 million.",
            "metadata": {"document_name": "QuarterlyReport.pdf", "page_number": 3},
            "similarity": 0.92,
        }
    ]

    # Test context building
    context = synthesizer.build_context(retrieved_chunks)
    assert '[Passage 1] Source: "QuarterlyReport.pdf" | Page: 3' in context

    # Test citation extraction
    mock_answer = "Revenue surged by 42% in Q3 reaching $12.5 million [QuarterlyReport.pdf, Page 3]."
    citations = synthesizer._extract_citations(mock_answer, retrieved_chunks)

    assert len(citations) >= 1
    assert citations[0].document_name == "QuarterlyReport.pdf"
    assert citations[0].page_number == 3
    assert citations[0].passage_preview is not None


@pytest.mark.asyncio
async def test_anti_hallucination_empty_context():
    synthesizer = RAGSynthesizer()
    result = await synthesizer.synthesize("What was the CEO's favorite book in 1995?", retrieved_chunks=[])
    assert result.answer == "I could not find the answer in your documents."
    assert len(result.citations) == 0
    assert result.grounded is False

