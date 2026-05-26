import pytest
from unittest.mock import patch, AsyncMock
import json
from app.services.export_service import cleanup_export_file


class TestExportCleanup:
    @pytest.mark.anyio
    async def test_removes_file_and_updates_redis(self):
        with patch("app.services.export_service.os.remove") as mock_remove:
            with patch("app.services.export_service.os.path.exists", return_value=True):
                with patch("app.services.export_service.redis_client.setex", new_callable=AsyncMock) as mock_setex:
                    await cleanup_export_file("job-123", "/tmp/test.xlsx", "xlsx")
        mock_remove.assert_called_once_with("/tmp/test.xlsx")
        mock_setex.assert_awaited_once()
        args = mock_setex.await_args.args
        assert args[0] == "export:job-123"
        assert args[1] == 300
        assert json.loads(args[2]) == {"status": "downloaded"}

    @pytest.mark.anyio
    async def test_skips_remove_when_file_missing(self):
        with patch("app.services.export_service.os.remove") as mock_remove:
            with patch("app.services.export_service.os.path.exists", return_value=False):
                with patch("app.services.export_service.redis_client.setex", new_callable=AsyncMock) as mock_setex:
                    await cleanup_export_file("job-123", "/tmp/ghost.csv", "csv")
        mock_remove.assert_not_called()
        mock_setex.assert_awaited_once()

    @pytest.mark.anyio
    async def test_handles_remove_error_gracefully(self):
        with patch("app.services.export_service.os.remove", side_effect=PermissionError("denied")):
            with patch("app.services.export_service.os.path.exists", return_value=True):
                with patch("app.services.export_service.redis_client.setex", new_callable=AsyncMock) as mock_setex:
                    await cleanup_export_file("job-123", "/tmp/test.pdf", "pdf")
        mock_setex.assert_awaited_once()
        data = json.loads(mock_setex.await_args.args[2])
        assert data["status"] == "downloaded"
