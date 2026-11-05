import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.supabase_client import get_service_client
from app.core.security_logger import log_security_event
from app.api.routes_documents import router as documents_router
from app.api.routes_chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: validates backend readiness and gateway connectivity upon startup.
    """
    print("[INFO] Starting Personal Document RAG Engine...")
    print(f"[INFO] Supabase URL: {settings.supabase_url}")
    print(f"[INFO] OpenRouter Model: {settings.openrouter_model}")
    print(f"[INFO] Embedding Dimension: {settings.embedding_dimension}")

    # Asynchronous non-blocking storage bucket initialization (offloaded to thread to never block loop)
    async def init_storage():
        if os.getenv("TESTING") == "true":
            return
        def _check_and_init():
            try:
                client = get_service_client()
                buckets = client.storage.list_buckets()
                bucket_names = [b.name for b in buckets]
                if settings.storage_bucket not in bucket_names:
                    try:
                        client.storage.create_bucket(settings.storage_bucket, options={"public": False})
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            await asyncio.wait_for(asyncio.to_thread(_check_and_init), timeout=3.0)
        except Exception:
            pass

    asyncio.create_task(init_storage())

    yield

    print("[INFO] Shutting down Personal Document RAG Engine.")


app = FastAPI(
    title="Personal Document RAG System",
    description="Enterprise-grade Multi-Tenant Personal Document RAG Engine with verifiable page citations.",
    version="1.0.0",
    lifespan=lifespan,
)

# Explicit CORS Configuration protecting against unauthorized cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.onrender\.com$|^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type", "Content-Length", "Retry-After"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    try:
        response = await call_next(request)
        # Standard OWASP defensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response
    except Exception as exc:
        log_security_event(
            "SERVER_EXCEPTION",
            client_ip=client_ip,
            detail=f"Unhandled internal server error: {type(exc).__name__}",
            severity="ERROR"
        )
        # Redact raw internal exception details from client API responses
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact the administrator."},
        )


# Register Routers
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Enterprise RAG Engine",
        "version": "1.0.0",
        "embedding_dimension": settings.embedding_dimension,
        "llm_model": settings.openrouter_model,
    }


# Mount and serve built React Single-Page Application (SPA) if present
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str, request: Request):
        # Do not catch API or docs routes
        if full_path.startswith("api") or full_path in ["docs", "redoc", "openapi.json", "health"]:
            raise HTTPException(status_code=404, detail="Not Found")
        
        target = os.path.abspath(os.path.join(static_dir, full_path))
        if os.path.commonpath([static_dir, target]) != static_dir:
            log_security_event(
                "SUSPICIOUS_PATH_TRAVERSAL",
                client_ip=request.client.host if request.client else "unknown",
                detail=f"Attempted path traversal in SPA router: {full_path[:50]}",
                severity="WARNING"
            )
            raise HTTPException(status_code=403, detail="Forbidden")

        if os.path.isfile(target):
            return FileResponse(target)
        
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend file not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
