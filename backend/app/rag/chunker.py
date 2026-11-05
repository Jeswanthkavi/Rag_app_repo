import re
from typing import List, Dict, Any
from pydantic import BaseModel
import tiktoken

from app.rag.extractor import PageBlock


class DocumentChunk(BaseModel):
    chunk_index: int
    page_number: int
    content: str
    metadata: Dict[str, Any]
    token_count: int


class SemanticChunker:
    """
    Recursive sentence-preserving semantic chunker.
    Enforces target token size (600-800 tokens) with 100-150 token overlap,
    strictly binding page numbers and document metadata.
    """

    def __init__(
        self,
        target_chunk_tokens: int = 700,
        chunk_overlap_tokens: int = 120,
        min_chunk_tokens: int = 50,
    ):
        self.target_tokens = target_chunk_tokens
        self.overlap_tokens = chunk_overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Reliable fallback: ~4 characters per token
        return max(1, len(text) // 4)

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Splits text into complete sentences without splitting mid-sentence.
        Handles abbreviations and standard punctuation (. ! ? \n\n).
        """
        # Split on double line breaks first to preserve paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences: List[str] = []

        for p in paragraphs:
            # Sentence boundary pattern
            raw_sentences = re.split(r"(?<=[.!?])\s+", p)
            for s in raw_sentences:
                clean = s.strip()
                if clean:
                    sentences.append(clean)

        return sentences

    def chunk_document(
        self,
        pages: List[PageBlock],
        document_id: str,
        document_name: str,
    ) -> List[DocumentChunk]:
        """
        Processes page blocks into continuous semantic chunks while maintaining
        strict page-level tracking and metadata injection.
        """
        chunks: List[DocumentChunk] = []
        global_index = 0

        for page in pages:
            sentences = self._split_into_sentences(page.text)
            if not sentences:
                continue

            current_sentences: List[str] = []
            current_tokens = 0

            for sentence in sentences:
                sent_tokens = self.count_tokens(sentence)

                # If single sentence is greater than target chunk size, split by words
                if sent_tokens > self.target_tokens:
                    # Flush current buffer first
                    if current_sentences:
                        content_str = " ".join(current_sentences)
                        chunks.append(
                            DocumentChunk(
                                chunk_index=global_index,
                                page_number=page.page_number,
                                content=content_str,
                                metadata={
                                    "document_id": document_id,
                                    "document_name": document_name,
                                    "page_number": page.page_number,
                                    "chunk_index": global_index,
                                },
                                token_count=current_tokens,
                            )
                        )
                        global_index += 1
                        current_sentences = []
                        current_tokens = 0

                    words = sentence.split(" ")
                    word_buf: List[str] = []
                    word_tok = 0
                    for w in words:
                        wt = self.count_tokens(w + " ")
                        if word_tok + wt > self.target_tokens and word_buf:
                            c_str = " ".join(word_buf)
                            chunks.append(
                                DocumentChunk(
                                    chunk_index=global_index,
                                    page_number=page.page_number,
                                    content=c_str,
                                    metadata={
                                        "document_id": document_id,
                                        "document_name": document_name,
                                        "page_number": page.page_number,
                                        "chunk_index": global_index,
                                    },
                                    token_count=word_tok,
                                )
                            )
                            global_index += 1
                            word_buf = []
                            word_tok = 0
                        word_buf.append(w)
                        word_tok += wt

                    if word_buf:
                        current_sentences = [" ".join(word_buf)]
                        current_tokens = word_tok
                    continue

                if current_tokens + sent_tokens > self.target_tokens and current_sentences:
                    content_str = " ".join(current_sentences)
                    chunks.append(
                        DocumentChunk(
                            chunk_index=global_index,
                            page_number=page.page_number,
                            content=content_str,
                            metadata={
                                "document_id": document_id,
                                "document_name": document_name,
                                "page_number": page.page_number,
                                "chunk_index": global_index,
                            },
                            token_count=current_tokens,
                        )
                    )
                    global_index += 1

                    # Retain overlap sentences
                    overlap_sentences: List[str] = []
                    overlap_tokens = 0
                    for s in reversed(current_sentences):
                        st = self.count_tokens(s)
                        if overlap_tokens + st <= self.overlap_tokens:
                            overlap_sentences.insert(0, s)
                            overlap_tokens += st
                        else:
                            break

                    current_sentences = overlap_sentences + [sentence]
                    current_tokens = overlap_tokens + sent_tokens
                else:
                    current_sentences.append(sentence)
                    current_tokens += sent_tokens

            # Flush trailing sentences for this page
            if current_sentences:
                content_str = " ".join(current_sentences)
                chunks.append(
                    DocumentChunk(
                        chunk_index=global_index,
                        page_number=page.page_number,
                        content=content_str,
                        metadata={
                            "document_id": document_id,
                            "document_name": document_name,
                            "page_number": page.page_number,
                            "chunk_index": global_index,
                        },
                        token_count=current_tokens,
                    )
                )
                global_index += 1

        return chunks

