import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.anyio
async def test_import_preview_route_ok():
    """Frontend calls /clients/import but backend route is /clients/import/preview.
    Test correct route exists and old wrong route returns 404."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Correct route: missing file → 422 (not 404)
        resp = await ac.post("/api/v1/clients/import/preview")
        assert resp.status_code == 422, "Preview route should exist (returns 422: missing file)"

        # Old wrong route: should not exist
        resp = await ac.post("/api/v1/clients/import")
        assert resp.status_code == 404, "Old /clients/import route should not exist"

@pytest.mark.anyio
async def test_import_confirm_accepts_body():
    """Confirm endpoint must accept { validation_id, rows } in POST body, not query params."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/clients/import/confirm", json={"rows": []})
        # Should not fail with 422 body validation error
        assert resp.status_code != 422, "Confirm endpoint should accept body with rows"
