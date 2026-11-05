from functools import lru_cache
from supabase import create_client, Client
from app.core.config import settings


@lru_cache()
def get_service_client() -> Client:
    """
    Returns a singleton Supabase client authenticated with the service role key.
    Used for backend background worker tasks, embedding ingestion, and admin actions.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured.")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_user_client(access_token: str) -> Client:
    """
    Returns a new Supabase client configured with the caller's JWT access token.
    Enforces Row Level Security (RLS) under the user's specific context.
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured.")
    
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    # Inject user auth token into postgrest headers
    client.postgrest.auth(access_token)
    return client

