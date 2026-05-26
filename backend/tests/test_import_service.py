import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import io
import openpyxl
from app.services.import_service import parse_and_validate, commit_import


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


class TestCommitImport:
    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        session.execute.return_value = result
        session.__aenter__.return_value = session
        session.__aexit__ = AsyncMock(return_value=None)
        session.add = MagicMock()
        session.rollback = AsyncMock()
        return session

    @pytest.mark.anyio
    async def test_imports_new_clients(self, mock_db_session):
        from app.schemas import ClientCreate
        from datetime import date
        rows = [
            ClientCreate(surname="Smith", given_name="John", father_name="Robert",
                         passport_number="AB123", nationality="US", travel_type_id=1,
                         travel_date=date(2027, 12, 1)),
        ]
        with patch("app.services.import_service.AsyncSessionLocal", return_value=mock_db_session):
            result = await commit_import("", rows)
        assert result["imported_count"] == 1
        assert result["duplicates_skipped"] == 0
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.anyio
    async def test_skips_existing_passports(self, mock_db_session):
        from app.schemas import ClientCreate
        from datetime import date
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = ["AB123"]
        rows = [
            ClientCreate(surname="Smith", given_name="John", father_name="Robert",
                         passport_number="AB123", nationality="US", travel_type_id=1,
                         travel_date=date(2027, 12, 1)),
            ClientCreate(surname="Doe", given_name="Jane", father_name="Jim",
                         passport_number="XY456", nationality="UK", travel_type_id=2,
                         travel_date=date(2027, 6, 15)),
        ]
        with patch("app.services.import_service.AsyncSessionLocal", return_value=mock_db_session):
            result = await commit_import("", rows)
        assert result["imported_count"] == 1
        assert result["duplicates_skipped"] == 1

    @pytest.mark.anyio
    async def test_rollback_on_db_error(self, mock_db_session):
        async def raise_db_error(*args, **kwargs):
            raise Exception("DB failure")
        mock_db_session.commit = raise_db_error
        from app.schemas import ClientCreate
        from datetime import date
        rows = [
            ClientCreate(surname="Smith", given_name="John", father_name="Robert",
                         passport_number="AB123", nationality="US", travel_type_id=1,
                         travel_date=date(2027, 12, 1)),
        ]
        with patch("app.services.import_service.AsyncSessionLocal", return_value=mock_db_session):
            with pytest.raises(Exception, match="DB failure"):
                await commit_import("", rows)
        mock_db_session.rollback.assert_awaited_once()

    @pytest.mark.anyio
    async def test_loads_from_redis_when_validation_id_provided(self, mock_db_session):
        from app.schemas import ClientCreate
        cached = b'{"rows": [{"surname": "Cache", "given_name": "Test", "father_name": "Foo", "passport_number": "CC123", "nationality": "FR", "travel_type_id": 1, "travel_date": "2027-12-01"}]}'
        with patch("app.services.import_service.redis_client.get", new_callable=AsyncMock, return_value=cached):
            with patch("app.services.import_service.AsyncSessionLocal", return_value=mock_db_session):
                result = await commit_import("test-vid", [])
        assert result["imported_count"] == 1
        assert result["duplicates_skipped"] == 0

    @pytest.mark.anyio
    async def test_falls_back_to_passed_rows_when_redis_empty(self, mock_db_session):
        from app.schemas import ClientCreate
        from datetime import date
        with patch("app.services.import_service.redis_client.get", new_callable=AsyncMock, return_value=None):
            with patch("app.services.import_service.AsyncSessionLocal", return_value=mock_db_session):
                rows = [
                    ClientCreate(surname="Fallback", given_name="User", father_name="P",
                                 passport_number="FB001", nationality="DE", travel_type_id=1,
                                 travel_date=date(2027, 12, 1)),
                ]
                result = await commit_import("test-vid", rows)
        assert result["imported_count"] == 1

    @pytest.mark.anyio
    async def test_response_keys(self, mock_db_session):
        from app.schemas import ClientCreate
        from datetime import date
        rows = [
            ClientCreate(surname="Smith", given_name="John", father_name="Robert",
                         passport_number="AB123", nationality="US", travel_type_id=1,
                         travel_date=date(2027, 12, 1)),
        ]
        with patch("app.services.import_service.AsyncSessionLocal", return_value=mock_db_session):
            result = await commit_import("", rows)
        assert list(result.keys()) == ["imported_count", "duplicates_skipped"]
