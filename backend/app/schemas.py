from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    error: dict[str, str] | None = None

class SessionResponse(BaseModel):
    id: UUID
    created_at: datetime

class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=120)

class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    message: str = Field(min_length=1, max_length=12000)
    mode: Literal["chat", "coding"] = "chat"

class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100000)
    category: str = Field(default="general", max_length=80)
    source: str = Field(default="manual", max_length=120)
