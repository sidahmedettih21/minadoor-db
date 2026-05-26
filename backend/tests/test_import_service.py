import pytest
from unittest.mock import patch, AsyncMock
import io
import openpyxl
from app.services.import_service import parse_and_validate


class TestParseAndValidate:
    VALID_CSV = (
        b"Surname,Given Name,Father Name,Passport Number,Nationality,"
        b"Travel Type,Travel Date\n"
        b"Smith,John,Robert,AB123456,USA,umrah,2027-12-01\n"
    )

    @pytest.mark.anyio
    @patch("app.services.import_service.redis_client.setex", new_callable=AsyncMock)
    async def test_valid_csv(self, mock_setex):
        result = await parse_and_validate(self.VALID_CSV, "test.csv")
        assert result["validation_id"] is not None
        assert result["total_rows"] == 1
        assert result["valid_rows"] == 1
        assert result["errors"] == []
        assert len(result["preview_data"]) == 1
        assert result["preview_data"][0]["surname"] == "Smith"
        mock_setex.assert_awaited_once()

    @pytest.mark.anyio
    @patch("app.services.import_service.redis_client.setex", new_callable=AsyncMock)
    async def test_csv_with_validation_errors(self, mock_setex):
        csv = (
            b"Surname,Given Name,Father Name,Passport Number,Nationality,"
            b"Travel Type,Travel Date\n"
            b",John,Robert,AB123456,USA,umrah,2027-12-01\n"
        )
        result = await parse_and_validate(csv, "test.csv")
        assert result["valid_rows"] == 0
        assert len(result["errors"]) > 0
        assert result["errors"][0]["field"] == "surname"

    @pytest.mark.anyio
    @patch("app.services.import_service.redis_client.setex", new_callable=AsyncMock)
    async def test_csv_with_duplicates(self, mock_setex):
        csv = (
            b"Surname,Given Name,Father Name,Passport Number,Nationality,"
            b"Travel Type,Travel Date\n"
            b"Smith,John,Robert,AB123456,USA,umrah,2027-12-01\n"
            b"Doe,Jane,Jim,AB123456,UK,visa,2027-06-01\n"
        )
        result = await parse_and_validate(csv, "test.csv")
        assert result["valid_rows"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["field"] == "passport_number"

    @pytest.mark.anyio
    @patch("app.services.import_service.redis_client.setex", new_callable=AsyncMock)
    async def test_valid_xlsx(self, mock_setex):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Surname", "Given Name", "Father Name", "Passport Number",
                    "Nationality", "Travel Type", "Travel Date"])
        ws.append(["Doe", "Jane", "Jim", "XY987654", "UK", "visa", "2027-06-15"])
        buf = io.BytesIO()
        wb.save(buf)
        wb.close()
        result = await parse_and_validate(buf.getvalue(), "test.xlsx")
        assert result["total_rows"] == 1
        assert result["valid_rows"] == 1
        assert result["errors"] == []

    @pytest.mark.anyio
    @patch("app.services.import_service.redis_client.setex", new_callable=AsyncMock)
    async def test_redis_failure_does_not_block(self, mock_setex):
        mock_setex.side_effect = ConnectionError("Redis down")
        result = await parse_and_validate(self.VALID_CSV, "test.csv")
        assert result["valid_rows"] == 1
        assert result["validation_id"] is not None

    @pytest.mark.anyio
    @patch("app.services.import_service.redis_client.setex", new_callable=AsyncMock)
    async def test_preview_limited_to_50_rows(self, mock_setex):
        header = b"Surname,Given Name,Father Name,Passport Number,Nationality,Travel Type,Travel Date\n"
        many_rows = header + b"".join(
            f"Doe{i},Jane,Foo,P{i:06d},US,umrah,2027-06-01\n".encode()
            for i in range(60)
        )
        result = await parse_and_validate(many_rows, "test.csv")
        assert result["total_rows"] == 60
        assert len(result["preview_data"]) == 50
