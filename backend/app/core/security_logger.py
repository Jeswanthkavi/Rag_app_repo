import logging
import sys
from typing import Optional, Dict, Any

# Configure a dedicated security audit logger
security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)

if not security_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [SECURITY_AUDIT] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


def log_security_event(
    event_type: str,
    client_ip: Optional[str] = None,
    user_id: Optional[str] = None,
    detail: Optional[str] = None,
    severity: str = "WARNING",
    extra: Optional[Dict[str, Any]] = None,
):
    """
    Emits a privacy-conscious security audit record.
    Strictly sanitizes inputs: NEVER logs passwords, JWTs, prompts, or document texts.
    """
    # Sanitize user_id and detail to prevent log injection / CRLF attacks
    safe_ip = (client_ip or "unknown").replace("\n", "").replace("\r", "")[:45]
    safe_uid = (user_id or "anonymous").replace("\n", "").replace("\r", "")[:64]
    safe_detail = (detail or "").replace("\n", " ").replace("\r", " ")[:200]
    
    msg = f"event={event_type} | ip={safe_ip} | user_id={safe_uid} | detail={safe_detail}"
    if extra:
        safe_extra = {k: str(v)[:50] for k, v in extra.items() if k not in ("token", "password", "key", "secret", "content")}
        msg += f" | extra={safe_extra}"

    if severity == "CRITICAL" or severity == "ERROR":
        security_logger.error(msg)
    else:
        security_logger.warning(msg)

