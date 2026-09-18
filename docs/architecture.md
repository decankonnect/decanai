# Decan AI architecture

The browser talks only to FastAPI. FastAPI owns the anonymous session cookie, validates uploads, retrieves session-scoped knowledge, calls the AI provider, and persists messages. Supabase is the durable system of record for sessions, conversations, documents, chunks, vectors, and feedback.

Retrieved text is labeled as untrusted reference context in the system prompt. It cannot override system instructions. PDF extraction currently handles text-layer PDFs; scanned PDFs return a clear OCR-not-enabled error. Image generation is intentionally a future service boundary.

Before public launch, add distributed rate-limit storage, signed storage paths, background processing for large PDFs, and a full browser test suite.
