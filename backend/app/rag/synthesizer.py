import json
import re
from typing import List, Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.core.config import settings


class Citation(BaseModel):
    document_id: Optional[str] = None
    document_name: str
    page_number: int
    passage_preview: Optional[str] = None
    similarity: Optional[float] = None


class SynthesisResult(BaseModel):
    answer: str
    citations: List[Citation]
    grounded: bool = True
    model_used: str


class RAGSynthesizer:
    """
    LLM Synthesizer with strict anti-hallucination guardrails,
    verifiable inline page citations, and fallback resilience.
    """

    def __init__(self):
        api_key = settings.openrouter_api_key or "sk-dummy"
        base_url = settings.openrouter_base_url
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=45.0,
        )
        self.model = settings.openrouter_model

    def build_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved passages with explicit source & page tags.
        """
        formatted_passages = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            metadata = chunk.get("metadata", {})
            doc_name = metadata.get("document_name") or chunk.get("document_name") or "Document"
            page_num = metadata.get("page_number") or chunk.get("page_number") or 1
            content = chunk.get("content", "").strip()

            formatted_passages.append(
                f'[Passage {idx}] Source: "{doc_name}" | Page: {page_num}\n{content}'
            )

        return "\n\n".join(formatted_passages)

    def _extract_citations(
        self, answer_text: str, retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Citation]:
        """
        Parses bracketed citations like [DocumentName.pdf, Page 4] from answer text
        and cross-references them against retrieved chunks.
        """
        citations: List[Citation] = []
        seen = set()

        # Regex pattern: [DocName.pdf, Page 4] or [DocName, Page 4]
        pattern = r"\[([^,\]]+?),\s*Page\s*(\d+)\]"
        matches = re.findall(pattern, answer_text, flags=re.IGNORECASE)

        for doc_name, page_str in matches:
            doc_name_clean = doc_name.strip().strip('"').strip("'")
            try:
                page_num = int(page_str.strip())
            except ValueError:
                page_num = 1

            key = (doc_name_clean.lower(), page_num)
            if key in seen:
                continue
            seen.add(key)

            # Find matching chunk for passage preview and document_id
            matched_chunk = None
            for chunk in retrieved_chunks:
                meta = chunk.get("metadata", {})
                c_name = meta.get("document_name") or chunk.get("document_name") or ""
                c_page = meta.get("page_number") or chunk.get("page_number") or 1
                if (
                    doc_name_clean.lower() in c_name.lower()
                    or c_name.lower() in doc_name_clean.lower()
                ) and int(c_page) == page_num:
                    matched_chunk = chunk
                    break

            if matched_chunk:
                preview = matched_chunk.get("content", "")[:200] + "..."
                sim = matched_chunk.get("similarity")
                doc_id = matched_chunk.get("document_id") or meta.get("document_id")
            else:
                preview = None
                sim = None
                doc_id = None

            citations.append(
                Citation(
                    document_id=str(doc_id) if doc_id else None,
                    document_name=doc_name_clean,
                    page_number=page_num,
                    passage_preview=preview,
                    similarity=sim,
                )
            )

        # If model answered with facts but missed brackets, link top chunk citations
        if not citations and retrieved_chunks and "could not find the answer" not in answer_text.lower():
            for chunk in retrieved_chunks[:2]:
                meta = chunk.get("metadata", {})
                d_name = meta.get("document_name") or chunk.get("document_name") or "Document"
                p_num = meta.get("page_number") or chunk.get("page_number") or 1
                key = (d_name.lower(), p_num)
                if key not in seen:
                    seen.add(key)
                    citations.append(
                        Citation(
                            document_id=str(chunk.get("document_id") or meta.get("document_id")),
                            document_name=d_name,
                            page_number=int(p_num),
                            passage_preview=chunk.get("content", "")[:200] + "...",
                            similarity=chunk.get("similarity"),
                        )
                    )

        return citations

    async def synthesize(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> SynthesisResult:
        """
        Executes strict anti-hallucination synthesis via OpenRouter with resilient fallback.
        """
        if not retrieved_chunks:
            return SynthesisResult(
                answer="I could not find the answer in your documents.",
                citations=[],
                grounded=False,
                model_used="guardrail-fallback",
            )

        context_str = self.build_context(retrieved_chunks)

        system_prompt = (
            "You are an enterprise AI document assistant. Your task is to answer the user's question using ONLY the provided document passages.\n\n"
            "STRICT RULES:\n"
            "1. Answer strictly using ONLY the provided document passages.\n"
            "2. Every factual claim MUST cite its source inline in the format: [DocumentName.pdf, Page X].\n"
            "3. If the answer cannot be found in the passages, state strictly: \"I could not find the answer in your documents.\"\n"
            "4. Zero extrapolation, zero outside knowledge, zero hallucination.\n"
            "5. Keep the answer professional, concise, and fully grounded."
        )

        user_content = f"CONTEXT PASSAGES:\n{context_str}\n\nUSER QUESTION:\n{query}"

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            # Include last 4 turns for conversational continuity
            for msg in chat_history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_content})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=800,
            )
            answer_text = response.choices[0].message.content or ""
            citations = self._extract_citations(answer_text, retrieved_chunks)

            return SynthesisResult(
                answer=answer_text,
                citations=citations,
                grounded=True,
                model_used=self.model,
            )

        except Exception as e:
            # Resilient Provider Fallback:
            # Fall back to top-matching passage directly rather than throwing 500
            return self._build_fallback_result(query, retrieved_chunks, str(e))

    async def synthesize_stream(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streams response via Server-Sent Events (SSE).
        Yields chunk tokens and terminates with a JSON metadata payload containing citations.
        """
        if not retrieved_chunks:
            yield "data: " + json.dumps({"token": "I could not find the answer in your documents."}) + "\n\n"
            yield "data: " + json.dumps({
                "done": True,
                "answer": "I could not find the answer in your documents.",
                "citations": []
            }) + "\n\n"
            return

        context_str = self.build_context(retrieved_chunks)

        system_prompt = (
            "You are an enterprise AI document assistant. Your task is to answer the user's question using ONLY the provided document passages.\n\n"
            "STRICT RULES:\n"
            "1. Answer strictly using ONLY the provided document passages.\n"
            "2. Every factual claim MUST cite its source inline in the format: [DocumentName.pdf, Page X].\n"
            "3. If the answer cannot be found in the passages, state strictly: \"I could not find the answer in your documents.\"\n"
            "4. Zero extrapolation, zero outside knowledge, zero hallucination."
        )

        user_content = f"CONTEXT PASSAGES:\n{context_str}\n\nUSER QUESTION:\n{query}"

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_content})

        accumulated_text = ""

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=800,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    accumulated_text += delta
                    yield "data: " + json.dumps({"token": delta}) + "\n\n"

            # Parse citations and yield terminal frame
            citations = self._extract_citations(accumulated_text, retrieved_chunks)
            yield "data: " + json.dumps({
                "done": True,
                "answer": accumulated_text,
                "citations": [c.model_dump() for c in citations]
            }) + "\n\n"

        except Exception as e:
            # Fallback stream
            fallback = self._build_fallback_result(query, retrieved_chunks, str(e))
            yield "data: " + json.dumps({"token": fallback.answer}) + "\n\n"
            yield "data: " + json.dumps({
                "done": True,
                "answer": fallback.answer,
                "citations": [c.model_dump() for c in fallback.citations],
                "fallback": True
            }) + "\n\n"

    def _build_fallback_result(
        self, query: str, retrieved_chunks: List[Dict[str, Any]], error_detail: str
    ) -> SynthesisResult:
        """
        Grounded excerpt from top matching passage when LLM gateway is unreachable or throttled.
        """
        top_chunk = retrieved_chunks[0]
        meta = top_chunk.get("metadata", {})
        doc_name = meta.get("document_name") or top_chunk.get("document_name") or "Document.pdf"
        page_num = meta.get("page_number") or top_chunk.get("page_number") or 1
        content_snippet = top_chunk.get("content", "").strip()

        answer = (
            f"Based on [{doc_name}, Page {page_num}]:\n\n"
            f"{content_snippet}"
        )

        citation = Citation(
            document_id=str(top_chunk.get("document_id") or meta.get("document_id")),
            document_name=doc_name,
            page_number=int(page_num),
            passage_preview=content_snippet[:200] + "...",
            similarity=top_chunk.get("similarity"),
        )

        return SynthesisResult(
            answer=answer,
            citations=[citation],
            grounded=True,
            model_used=f"resilient-fallback ({error_detail[:50]})",
        )

