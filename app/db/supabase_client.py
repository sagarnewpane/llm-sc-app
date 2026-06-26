from typing import Optional

from supabase import create_client, Client

from app.core.config import get_settings

settings = get_settings()

_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client
