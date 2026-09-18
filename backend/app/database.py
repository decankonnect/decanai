from typing import Any
import httpx
from .config import get_settings

class Database:
    def __init__(self) -> None:
        settings = get_settings()
        self.base = settings.supabase_url.rstrip("/") + "/rest/v1" if settings.supabase_url else ""
        self.key = settings.supabase_service_role_key

    @property
    def configured(self) -> bool:
        return bool(self.base and self.key)

    async def request(self, method: str, table: str, *, params: dict[str, str] | None = None, json: Any = None, headers: dict[str, str] | None = None) -> Any:
        if not self.configured:
            raise RuntimeError("Supabase is not configured")
        request_headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json", **(headers or {})}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, f"{self.base}/{table}", params=params, json=json, headers=request_headers)
            response.raise_for_status()
            return response.json() if response.content else None

db = Database()
