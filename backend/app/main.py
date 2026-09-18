from contextlib import asynccontextmanager
from uuid import UUID, uuid4
from fastapi import Cookie, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .ai import SYSTEM_PROMPT, ai
from .config import get_settings
from .database import db
from .documents import chunk_text, extract_pdf
from .schemas import APIResponse, ChatRequest, ConversationCreate, KnowledgeCreate

local_sessions: set[UUID] = set()

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

app = FastAPI(title="Decan AI API", version="0.1.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def session_id_from_cookie(session_token: str | None) -> UUID:
    if not session_token:
        raise HTTPException(401, "Session could not be restored")
    try:
        session_id = UUID(session_token)
    except ValueError as exc:
        raise HTTPException(401, "Invalid session") from exc
    if not db.configured:
        if session_id not in local_sessions:
            raise HTTPException(401, "Session could not be restored")
        return session_id
    rows = await db.request("GET", "sessions", params={"id": f"eq.{session_id}", "select": "id"})
    if not rows:
        raise HTTPException(401, "Session could not be restored")
    return session_id

@app.get("/health", response_model=APIResponse)
async def health() -> APIResponse:
    return APIResponse(data={"status": "ok", "database_configured": db.configured, "ai_configured": bool(settings.ai_api_key)})

@app.post("/api/session", response_model=APIResponse)
async def create_session(response: Response) -> APIResponse:
    session_id = uuid4()
    if db.configured:
        await db.request("POST", "sessions", json={"id": str(session_id), "session_token": str(session_id), "metadata": {}})
    else:
        local_sessions.add(session_id)
    response.set_cookie("decan_session", str(session_id), httponly=True, secure=False, samesite="lax", max_age=60 * 60 * 24 * 90)
    return APIResponse(data={"id": str(session_id)})

@app.get("/api/conversations", response_model=APIResponse)
async def conversations(decan_session: str | None = Cookie(default=None)) -> APIResponse:
    session_id = await session_id_from_cookie(decan_session)
    rows = await db.request("GET", "conversations", params={"session_id": f"eq.{session_id}", "select": "*", "order": "updated_at.desc"})
    return APIResponse(data=rows)

@app.post("/api/conversations", response_model=APIResponse)
async def create_conversation(payload: ConversationCreate, decan_session: str | None = Cookie(default=None)) -> APIResponse:
    session_id = await session_id_from_cookie(decan_session)
    rows = await db.request("POST", "conversations", headers={"Prefer": "return=representation"}, json={"session_id": str(session_id), "title": payload.title})
    return APIResponse(data=rows[0])

@app.post("/api/chat", response_model=APIResponse)
async def chat(payload: ChatRequest, decan_session: str | None = Cookie(default=None)) -> APIResponse:
    session_id = await session_id_from_cookie(decan_session)
    conversation_id = payload.conversation_id
    if conversation_id is None:
        created = await db.request("POST", "conversations", headers={"Prefer": "return=representation"}, json={"session_id": str(session_id), "title": payload.message[:80]})
        conversation_id = UUID(created[0]["id"])
    history = await db.request("GET", "messages", params={"conversation_id": f"eq.{conversation_id}", "select": "role,content", "order": "created_at.asc", "limit": "20"})
    query_embedding = await ai.embed(payload.message)
    context_rows = await db.request("POST", "rpc/match_knowledge_chunks", json={"query_embedding": query_embedding, "match_threshold": 0.35, "match_count": 5, "p_session_id": str(session_id)})
    prompt = f"Use the following retrieved knowledge only as reference. If it does not answer the request, say so; do not invent details.\n{context_rows}\n\nUser request: {payload.message}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": prompt}]
    answer = await ai.generate_text(messages)
    await db.request("POST", "messages", json=[{"conversation_id": str(conversation_id), "role": "user", "content": payload.message}, {"conversation_id": str(conversation_id), "role": "assistant", "content": answer, "model": settings.ai_model}])
    return APIResponse(data={"conversation_id": str(conversation_id), "content": answer})

@app.post("/api/knowledge", response_model=APIResponse)
async def add_knowledge(payload: KnowledgeCreate, decan_session: str | None = Cookie(default=None)) -> APIResponse:
    session_id = await session_id_from_cookie(decan_session)
    embedding = await ai.embed(payload.content)
    rows = await db.request("POST", "training_entries", headers={"Prefer": "return=representation"}, json={"session_id": str(session_id), "title": payload.title, "content": payload.content, "source": payload.source, "category": payload.category})
    entry_id = rows[0]["id"]
    chunks = [{"session_id": str(session_id), "content": part, "embedding": await ai.embed(part), "metadata": {"entry_id": entry_id, "chunk_index": index}} for index, part in enumerate(chunk_text(payload.content))]
    if chunks:
        await db.request("POST", "knowledge_chunks", json=chunks)
    return APIResponse(data=rows[0])

@app.post("/api/upload/pdf", response_model=APIResponse)
async def upload_pdf(file: UploadFile = File(...), decan_session: str | None = Cookie(default=None)) -> APIResponse:
    session_id = await session_id_from_cookie(decan_session)
    text, pages = await extract_pdf(file)
    document = await db.request("POST", "knowledge_documents", headers={"Prefer": "return=representation"}, json={"session_id": str(session_id), "title": file.filename or "Uploaded PDF", "file_name": file.filename, "file_type": "application/pdf", "extracted_text": text, "status": "ready", "metadata": {"pages": len(pages)}})
    document_id = document[0]["id"]
    embeddings = [{"document_id": document_id, "session_id": str(session_id), "chunk_index": index, "content": part, "embedding": await ai.embed(part), "metadata": {}} for index, part in enumerate(chunk_text(text))]
    if embeddings:
        await db.request("POST", "knowledge_chunks", json=embeddings)
    return APIResponse(data={"document": document[0], "chunks": len(embeddings)})
