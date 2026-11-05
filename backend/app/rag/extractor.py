import io
import os
from typing import List, Union
from pydantic import BaseModel
import pdfplumber
import pypdf
from app.core.config import settings


class PageBlock(BaseModel):
    page_number: int
    text: str
    metadata: dict = {}


class DocumentExtractor:
    """
    Layout-aware text extraction for PDF, TXT, and Markdown documents.
    Preserves exact page numbers and layout integrity.
    """

    @classmethod
    def extract(cls, file_content: Union[bytes, str], mime_type: str = "application/pdf") -> List[PageBlock]:
        """
        Extracts structured page-level text from raw file bytes or string.
        """
        if "pdf" in mime_type.lower() or (isinstance(file_content, bytes) and file_content.startswith(b"%PDF")):
            return cls._extract_pdf(file_content)
        else:
            return cls._extract_plaintext(file_content)

    @classmethod
    def _extract_pdf(cls, content: Union[bytes, str]) -> List[PageBlock]:
        blocks: List[PageBlock] = []
        stream = io.BytesIO(content) if isinstance(content, bytes) else open(content, "rb")
        max_pages = getattr(settings, "max_pdf_pages", 250)

        try:
            with pdfplumber.open(stream) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    if idx > max_pages:
                        print(f"[SECURITY] Maximum page limit ({max_pages}) reached. Truncating extraction.")
                        break

                    # 1. Layout-aware text extraction
                    page_text = page.extract_text(layout=True) or ""
                    
                    # 2. Extract tables and convert to markdown table format for layout fidelity
                    try:
                        tables = page.extract_tables()
                        table_markdowns = []
                        for table in tables:
                            if not table or len(table) < 1:
                                continue
                            # Filter empty rows
                            clean_rows = [[str(cell or "").strip().replace("\n", " ") for cell in row] for row in table]
                            if not clean_rows:
                                continue
                            headers = clean_rows[0]
                            header_line = "| " + " | ".join(headers) + " |"
                            sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
                            data_lines = ["| " + " | ".join(row) + " |" for row in clean_rows[1:]]
                            table_markdowns.append("\n" + "\n".join([header_line, sep_line] + data_lines) + "\n")
                        
                        if table_markdowns:
                            page_text += "\n\n### Extracted Tables:\n" + "\n".join(table_markdowns)
                    except Exception:
                        pass  # Table parsing best-effort

                    clean_text = page_text.strip()
                    if clean_text:
                        blocks.append(PageBlock(page_number=idx, text=clean_text))

        except Exception as e:
            # Fallback to pypdf if pdfplumber fails
            stream.seek(0)
            try:
                reader = pypdf.PdfReader(stream)
                for idx, page in enumerate(reader.pages, start=1):
                    if idx > max_pages:
                        break
                    txt = page.extract_text() or ""
                    if txt.strip():
                        blocks.append(PageBlock(page_number=idx, text=txt.strip()))
            except Exception as fallback_err:
                raise RuntimeError(f"PDF extraction failed completely: {e} | Fallback: {fallback_err}")
        finally:
            if not isinstance(content, bytes) and hasattr(stream, "close"):
                stream.close()

        if not blocks:
            # If empty PDF or scanned without OCR, provide a placeholder page
            blocks.append(PageBlock(page_number=1, text="[Document contains no extractable text]"))

        return blocks

    @classmethod
    def _extract_plaintext(cls, content: Union[bytes, str]) -> List[PageBlock]:
        if isinstance(content, bytes):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1", errors="replace")
        else:
            text = content

        text = text.strip()
        if not text:
            return [PageBlock(page_number=1, text="[Empty document]")]

        # For text files, if large, paginate by ~4000 chars per page
        page_size = 4000
        blocks: List[PageBlock] = []
        if len(text) <= page_size:
            blocks.append(PageBlock(page_number=1, text=text))
        else:
            total_pages = (len(text) + page_size - 1) // page_size
            for i in range(total_pages):
                start = i * page_size
                end = min(start + page_size, len(text))
                blocks.append(PageBlock(page_number=i + 1, text=text[start:end]))

        return blocks

