from typing import Optional
from pydantic import BaseModel
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.config import settings
from app.core.supabase_client import get_service_client
from app.core.security_logger import log_security_event

security = HTTPBearer(auto_error=True)


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    access_token: str
    role: Optional[str] = "authenticated"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """
    Validates Supabase JWT against Supabase Auth API and cryptographically verifies token validity.
    Defense-in-depth: Never allows unverified JWT signature bypass.
    """
    token = credentials.credentials
    client_ip = request.client.host if request.client else "unknown"

    if not token or not token.strip():
        log_security_event("AUTH_FAILURE", client_ip=client_ip, detail="Empty bearer token supplied")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Primary verification: Supabase Auth server-side verification
    try:
        client = get_service_client()
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            user = user_response.user
            return AuthenticatedUser(
                user_id=str(user.id),
                email=user.email or "",
                access_token=token,
                role=getattr(user, "role", "authenticated") or "authenticated"
            )
    except Exception as auth_err:
        # Supabase API call failed - check if cryptographically verifiable via JWT Secret
        if settings.supabase_jwt_secret:
            try:
                verified_payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_signature": True, "verify_exp": True},
                )
                sub = verified_payload.get("sub")
                if sub:
                    return AuthenticatedUser(
                        user_id=str(sub),
                        email=verified_payload.get("email", ""),
                        access_token=token,
                        role=verified_payload.get("role", "authenticated")
                    )
            except jwt.ExpiredSignatureError:
                log_security_event("AUTH_FAILURE", client_ip=client_ip, detail="Expired JWT signature presented")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired. Please sign in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except jwt.InvalidTokenError as token_err:
                log_security_event(
                    "AUTH_FORGERY_ATTEMPT",
                    client_ip=client_ip,
                    detail=f"Cryptographic signature check failed: {type(token_err).__name__}",
                    severity="ERROR"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Cryptographically invalid authentication credentials.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        log_security_event(
            "AUTH_FAILURE",
            client_ip=client_ip,
            detail="Supabase Auth verification failed and no valid signature found",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_security_event("AUTH_FAILURE", client_ip=client_ip, detail="Unresolvable authentication credentials")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

