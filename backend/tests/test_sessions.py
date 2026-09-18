from fastapi import Response
import pytest

from app.main import create_session, db, local_sessions


@pytest.mark.anyio
async def test_create_session_works_without_supabase():
    if db.configured:
        pytest.skip("This test covers local development mode")

    local_sessions.clear()
    response = Response()

    payload = await create_session(response)

    session_id = payload.data["id"]
    assert session_id in {str(value) for value in local_sessions}
    assert response.headers["set-cookie"].startswith("decan_session=")
