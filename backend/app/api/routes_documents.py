import os
import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from pydantic import BaseModel

from app.api.auth_middleware import get_current_user, AuthenticatedUser
from app.core.config import settings
from app.core.supabase_client import get_service_client
from app.core.security_logger import log_security_event
from app.core.rate_limiter import rate_limiter
from app.rag.extractor import DocumentExtractor
from app.rag.chunker import SemanticChunker
from app.rag.embeddings import EmbeddingGenerator

router = APIRouter(prefix="/api/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    id: str
    name: str
    storage_path: str
    file_size: int
    mime_type: str
    page_count: int
    status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    page_count: int
    error_message: Optional[str] = None


async def process_document_pipeline(
    document_id: str,
    user_id: str,
    document_name: str,
    file_bytes: bytes,
    mime_type: str,
):
    """
    Background worker that executes the complete RAG ingestion pipeline:
    1. Update status to 'processing'
    2. Extract layout-aware page blocks
    3. Generate semantic chunks with metadata
    4. Batch generate vector embeddings (768-dim)
    5. Persist chunks in Supabase document_chunks table
    6. Transition status to 'completed' (or 'failed' on error with cleanup)
    """
    client = get_service_client()
    try:
        # Step 1: Update status to processing
        client.table("documents").update({
            "status": "processing",
            "updated_at": "now()"
        }).eq("id", document_id).execute()

        # Step 2: Extraction
        page_blocks = DocumentExtractor.extract(file_bytes, mime_type)
        page_count = len(page_blocks)

        # Step 3: Chunking
        chunker = SemanticChunker(target_chunk_tokens=700, chunk_overlap_tokens=120)
        chunks = chunker.chunk_document(
            pages=page_blocks,
            document_id=document_id,
            document_name=document_name,
        )

        if not chunks:
            raise ValueError("No text could be extracted or chunked from the document.")

        # Step 4: Batch Vector Embeddings
        chunk_texts = [c.content for c in chunks]
        embedder = EmbeddingGenerator(dimension=settings.embedding_dimension)
        embeddings = await embedder.generate_embeddings(chunk_texts)

        # Step 5: Insert document_chunks in batches of 50
        records = []
        for c, emb in zip(chunks, embeddings):
            records.append({
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "content": c.content,
                "metadata": c.metadata,
                "embedding": emb,
            })

        batch_size = 50
        for i in range(0, len(records), batch_size):
            sub_batch = records[i : i + batch_size]
            client.table("document_chunks").insert(sub_batch).execute()

        # Step 6: Mark completed
        client.table("documents").update({
            "status": "completed",
            "page_count": page_count,
            "error_message": None,
            "updated_at": "now()"
        }).eq("id", document_id).execute()

    except Exception as e:
        error_msg = str(e)
        # Atomic failure state transition and cleanup
        try:
            client.table("document_chunks").delete().eq("document_id", document_id).execute()
            client.table("documents").update({
                "status": "failed",
                "error_message": error_msg[:500],
                "updated_at": "now()"
            }).eq("id", document_id).execute()
        except Exception:
            pass


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Uploads a document (.pdf, .txt, .md) to Supabase Storage with strict size limits,
    magic byte verification, sanitization, and asynchronous background ingestion.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Enforce upload rate limit to protect storage and embedding quota
    rate_limiter.check_rate_limit(
        request=request,
        endpoint_tag="document_upload",
        max_requests=settings.rate_limit_upload_per_minute,
        window_seconds=60.0,
    )

    # 1. Filename sanitization against path traversal / injection attacks
    raw_filename = os.path.basename(file.filename or "document.pdf")
    clean_filename = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', raw_filename).strip()
    if not clean_filename or len(clean_filename) > 120:
        clean_filename = f"doc_{uuid.uuid4().hex[:8]}.pdf"

    # File extension check
    lower_name = clean_filename.lower()
    if not any(lower_name.endswith(ext) for ext in [".pdf", ".docx", ".doc", ".txt", ".md"]):
        log_security_event(
            "MALICIOUS_FILE_BLOCKED",
            client_ip=client_ip,
            user_id=current_user.user_id,
            detail=f"Rejected unsupported extension for file {clean_filename}",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only verified .pdf, .docx, .txt, and .md files are allowed."
        )

    # 2. Bounded stream reading to enforce strict size ceiling (Anti-DoS)
    max_size = settings.max_upload_size_bytes
    chunk_size = 64 * 1024  # 64 KB chunks
    total_bytes = bytearray()

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes.extend(chunk)
        if len(total_bytes) > max_size:
            log_security_event(
                "OVERSIZED_UPLOAD_REJECTED",
                client_ip=client_ip,
                user_id=current_user.user_id,
                detail=f"Upload exceeded maximum limit of {max_size // (1024*1024)}MB",
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum permitted size of {max_size // (1024 * 1024)} MB."
            )

    file_bytes = bytes(total_bytes)
    file_size = len(file_bytes)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # 3. Magic byte signature verification (Anti-MIME spoofing)
    content_type = file.content_type or "application/octet-stream"
    if lower_name.endswith(".pdf"):
        if not file_bytes.startswith(b"%PDF-"):
            log_security_event(
                "MALICIOUS_FILE_BLOCKED",
                client_ip=client_ip,
                user_id=current_user.user_id,
                detail=f"PDF magic byte header missing for {clean_filename}",
                severity="ERROR"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file content: The file is not a valid PDF document."
            )
        content_type = "application/pdf"
    elif lower_name.endswith((".docx", ".doc")):
        if not file_bytes.startswith(b"PK"):
            log_security_event(
                "MALICIOUS_FILE_BLOCKED",
                client_ip=client_ip,
                user_id=current_user.user_id,
                detail=f"DOCX zip header missing for {clean_filename}",
                severity="ERROR"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file content: The file is not a valid Word (.docx) document."
            )
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif lower_name.endswith((".txt", ".md")):
        # Ensure text is valid UTF-8 and contains no embedded binary null bytes
        if b"\x00" in file_bytes:
            log_security_event(
                "MALICIOUS_FILE_BLOCKED",
                client_ip=client_ip,
                user_id=current_user.user_id,
                detail=f"Disguised binary null bytes detected in text upload {clean_filename}",
                severity="ERROR"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text document: Binary null characters detected."
            )
        try:
            file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text document must be valid UTF-8 encoded."
            )
        content_type = "text/plain" if lower_name.endswith(".txt") else "text/markdown"

    doc_id = str(uuid.uuid4())
    safe_storage_name = f"{uuid.uuid4().hex[:8]}_{clean_filename}"
    storage_path = f"{current_user.user_id}/{safe_storage_name}"

    client = get_service_client()

    # 4. Upload file to Supabase Storage bucket
    try:
        client.storage.from_(settings.storage_bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception:
        pass

    # 5. Insert document metadata with status 'pending'
    doc_record = {
        "id": doc_id,
        "user_id": current_user.user_id,
        "name": clean_filename,
        "storage_path": storage_path,
        "file_size": file_size,
        "mime_type": content_type,
        "page_count": 1,
        "status": "pending",
        "error_message": None,
    }

    try:
        res = client.table("documents").insert(doc_record).execute()
        created_data = res.data[0] if res.data else doc_record
    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error registering document metadata."
        )

    # 6. Schedule asynchronous RAG ingestion pipeline
    background_tasks.add_task(
        process_document_pipeline,
        document_id=doc_id,
        user_id=current_user.user_id,
        document_name=clean_filename,
        file_bytes=file_bytes,
        mime_type=content_type,
    )

    return DocumentResponse(
        id=doc_id,
        name=filename,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=content_type,
        page_count=1,
        status="pending",
        created_at=created_data.get("created_at", ""),
        updated_at=created_data.get("updated_at", ""),
    )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Lists all documents owned by the authenticated tenant.
    """
    client = get_service_client()
    try:
        res = (
            client.table("documents")
            .select("*")
            .eq("user_id", current_user.user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [
            DocumentResponse(
                id=d["id"],
                name=d["name"],
                storage_path=d["storage_path"],
                file_size=d["file_size"],
                mime_type=d["mime_type"],
                page_count=d.get("page_count", 1),
                status=d["status"],
                error_message=d.get("error_message"),
                created_at=d.get("created_at", ""),
                updated_at=d.get("updated_at", ""),
            )
            for d in (res.data or [])
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}"
        )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Polling endpoint for document ingestion status.
    """
    client = get_service_client()
    try:
        res = (
            client.table("documents")
            .select("id, status, page_count, error_message")
            .eq("id", document_id)
            .eq("user_id", current_user.user_id)
            .maybe_single()
            .execute()
        )
        if not res or not res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        data = res.data
        return DocumentStatusResponse(
            id=data["id"],
            status=data["status"],
            page_count=data.get("page_count", 1),
            error_message=data.get("error_message"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Deletes document record, cascading its document_chunks, and deletes the storage object.
    Strictly verifies tenant ownership.
    """
    client = get_service_client()
    client_ip = request.client.host if request.client else "unknown"

    try:
        # 1. Fetch document to verify existence and ownership
        res = (
            client.table("documents")
            .select("id, user_id, storage_path")
            .eq("id", document_id)
            .maybe_single()
            .execute()
        )
        if not res or not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        doc_data = res.data
        if doc_data.get("user_id") != current_user.user_id:
            log_security_event(
                "CROSS_TENANT_ACCESS_DENIED",
                client_ip=client_ip,
                user_id=current_user.user_id,
                detail=f"Denied attempt to delete document {document_id[:8]} belonging to another tenant",
                severity="CRITICAL"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot delete another tenant's document."
            )

        storage_path = doc_data.get("storage_path")

        # 2. Delete storage file if path exists
        if storage_path:
            try:
                client.storage.from_(settings.storage_bucket).remove([storage_path])
            except Exception:
                pass

        # 3. Delete document row (cascades to document_chunks)
        client.table("documents").delete().eq("id", document_id).eq("user_id", current_user.user_id).execute()

        return {"success": True, "message": "Document and associated vector chunks deleted successfully."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document."
        )

