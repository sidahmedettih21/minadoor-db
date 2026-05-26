import pytest
import os
import io
import openpyxl
from datetime import date
from app.services.import_parser import HEADER_ALIASES, resolve_field, parse_csv, parse_xlsx, validate_rows


class TestResolveField:
    def test_english_surname(self):
        assert resolve_field("Surname") == "surname"
        assert resolve_field("surname") == "surname"

    def test_english_given_name(self):
        assert resolve_field("Given Name") == "given_name"
        assert resolve_field("given name") == "given_name"

    def test_english_father_name(self):
        assert resolve_field("Father Name") == "father_name"

    def test_english_mother_name(self):
        assert resolve_field("Mother Name") == "mother_name"

    def test_english_passport_number_aliases(self):
        assert resolve_field("Passport Number") == "passport_number"
        assert resolve_field("Passport No") == "passport_number"
        assert resolve_field("Passport #") == "passport_number"

    def test_english_nationality(self):
        assert resolve_field("Nationality") == "nationality"

    def test_english_date_of_birth_aliases(self):
        assert resolve_field("Date of Birth") == "date_of_birth"
        assert resolve_field("DOB") == "date_of_birth"

    def test_english_passport_issue_date(self):
        assert resolve_field("Passport Issue") == "passport_issue_date"
        assert resolve_field("Passport Issue Date") == "passport_issue_date"

    def test_english_passport_expiry(self):
        assert resolve_field("Passport Expiry") == "passport_expiry"
        assert resolve_field("Passport Expiry Date") == "passport_expiry"

    def test_english_gender(self):
        assert resolve_field("Gender") == "gender"
        assert resolve_field("Sex") == "gender"

    def test_english_travel_type(self):
        assert resolve_field("Travel Type") == "travel_type_id"

    def test_english_travel_date(self):
        assert resolve_field("Travel Date") == "travel_date"

    def test_english_payment_method_aliases(self):
        assert resolve_field("Payment Method") == "payment_method"
        assert resolve_field("Payment") == "payment_method"

    def test_english_status(self):
        assert resolve_field("Status") == "status"

    def test_english_notes(self):
        assert resolve_field("Notes") == "notes"
        assert resolve_field("Remarks") == "notes"

    def test_french_surname(self):
        assert resolve_field("Nom") == "surname"

    def test_french_given_name(self):
        assert resolve_field("Prénom") == "given_name"

    def test_french_father_name(self):
        assert resolve_field("Nom du père") == "father_name"

    def test_french_mother_name(self):
        assert resolve_field("Nom de la mère") == "mother_name"

    def test_french_passport_number(self):
        assert resolve_field("N° Passeport") == "passport_number"
        assert resolve_field("Numéro de passeport") == "passport_number"
        assert resolve_field("Passeport") == "passport_number"

    def test_french_nationality(self):
        assert resolve_field("Nationalité") == "nationality"

    def test_french_date_of_birth(self):
        assert resolve_field("Date de naissance") == "date_of_birth"

    def test_french_passport_issue_date(self):
        assert resolve_field("Date d'émission") == "passport_issue_date"

    def test_french_passport_expiry(self):
        assert resolve_field("Date d'expiration") == "passport_expiry"

    def test_french_gender(self):
        assert resolve_field("Genre") == "gender"
        assert resolve_field("Sexe") == "gender"

    def test_french_travel_type(self):
        assert resolve_field("Type de voyage") == "travel_type_id"

    def test_french_travel_date(self):
        assert resolve_field("Date de voyage") == "travel_date"

    def test_french_payment_method(self):
        assert resolve_field("Mode de paiement") == "payment_method"
        assert resolve_field("Paiement") == "payment_method"

    def test_french_status(self):
        assert resolve_field("Statut") == "status"

    def test_french_notes(self):
        assert resolve_field("Remarques") == "notes"

    def test_arabic_surname(self):
        assert resolve_field("اللقب") == "surname"

    def test_arabic_given_name(self):
        assert resolve_field("الاسم") == "given_name"

    def test_arabic_father_name(self):
        assert resolve_field("اسم الأب") == "father_name"

    def test_arabic_mother_name(self):
        assert resolve_field("اسم الأم") == "mother_name"

    def test_arabic_passport_number(self):
        assert resolve_field("جواز السفر") == "passport_number"
        assert resolve_field("رقم جواز السفر") == "passport_number"

    def test_arabic_nationality(self):
        assert resolve_field("الجنسية") == "nationality"

    def test_arabic_date_of_birth(self):
        assert resolve_field("تاريخ الميلاد") == "date_of_birth"

    def test_arabic_passport_issue_date(self):
        assert resolve_field("تاريخ الإصدار") == "passport_issue_date"

    def test_arabic_passport_expiry(self):
        assert resolve_field("تاريخ الانتهاء") == "passport_expiry"

    def test_arabic_gender(self):
        assert resolve_field("الجنس") == "gender"

    def test_arabic_travel_type(self):
        assert resolve_field("نوع السفر") == "travel_type_id"

    def test_arabic_travel_date(self):
        assert resolve_field("تاريخ السفر") == "travel_date"

    def test_arabic_payment_method(self):
        assert resolve_field("طريقة الدفع") == "payment_method"
        assert resolve_field("الدفع") == "payment_method"

    def test_arabic_status(self):
        assert resolve_field("الحالة") == "status"

    def test_arabic_notes(self):
        assert resolve_field("ملاحظات") == "notes"

    def test_case_insensitive(self):
        assert resolve_field("SURNAME") == "surname"
        assert resolve_field("given NAME") == "given_name"
        assert resolve_field("PASSEPORT") == "passport_number"

    def test_whitespace_trimmed(self):
        assert resolve_field("  Surname  ") == "surname"
        assert resolve_field("\tGiven Name\n") == "given_name"

    def test_unknown_header_returns_none(self):
        assert resolve_field("Nonexistent Column") is None
        assert resolve_field("") is None

    def test_aliases_dict_contains_all_languages(self):
        assert "en" in HEADER_ALIASES
        assert "fr" in HEADER_ALIASES
        assert "ar" in HEADER_ALIASES


class TestParseCsv:
    def test_parse_valid_csv(self):
        raw = b"Surname,Given Name,Father Name,Mother Name,Passport Number,Nationality,Travel Date\nSmith,John,Robert,Maria,AB1234567,USA,2027-12-01\n"
        result = parse_csv(raw)
        assert len(result) == 1
        assert result[0]["surname"] == "Smith"
        assert result[0]["given_name"] == "John"
        assert result[0]["father_name"] == "Robert"
        assert result[0]["passport_number"] == "AB1234567"
        assert result[0]["nationality"] == "USA"
        assert result[0]["travel_date"] == "2027-12-01"

    def test_parse_with_bom(self):
        raw = b"\xef\xbb\xbfSurname,Given Name\nDoe,John\n"
        result = parse_csv(raw)
        assert len(result) == 1
        assert result[0]["surname"] == "Doe"

    def test_parse_latin1_french_headers(self):
        raw = "Nom,Prénom,Date de naissance\nDupont,Jean,1990-05-15\n".encode("latin-1")
        result = parse_csv(raw)
        assert len(result) == 1
        assert result[0]["surname"] == "Dupont"
        assert result[0]["given_name"] == "Jean"
        assert result[0]["date_of_birth"] == "1990-05-15"

    def test_parse_arabic_headers(self):
        raw = "اللقب,الاسم,تاريخ السفر\nمحمد,أحمد,2027-06-15\n".encode("utf-8")
        result = parse_csv(raw)
        assert len(result) == 1
        assert result[0]["surname"] == "محمد"
        assert result[0]["given_name"] == "أحمد"
        assert result[0]["travel_date"] == "2027-06-15"

    def test_unknown_headers_silently_dropped(self):
        raw = b"Surname,FooColumn,Given Name\nDoe,bar,John\n"
        result = parse_csv(raw)
        assert len(result) == 1
        assert "foocolumn" not in result[0]
        assert result[0]["surname"] == "Doe"
        assert result[0]["given_name"] == "John"

    def test_empty_bytes_returns_empty_list(self):
        assert parse_csv(b"") == []

    def test_whitespace_only_bytes_returns_empty_list(self):
        assert parse_csv(b"   \n\n  ") == []

    def test_header_only_no_data_rows(self):
        raw = b"Surname,Given Name\n"
        result = parse_csv(raw)
        assert result == []

    def test_skip_empty_data_rows(self):
        raw = b"Surname,Given Name\nDoe,John\n,\n\n"
        result = parse_csv(raw)
        assert len(result) == 1
        assert result[0]["surname"] == "Doe"

    def test_parse_from_actual_fixture_file(self):
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "valid_en.csv")
        with open(fixture_path, "rb") as f:
            content = f.read()
        result = parse_csv(content)
        assert len(result) == 1
        assert result[0]["surname"] == "Smith"
        assert result[0]["given_name"] == "John"
        assert result[0]["father_name"] == "Robert"
        assert result[0]["passport_number"] == "AB1234567"
        assert result[0]["travel_date"] == "2027-12-01"
        assert result[0]["mother_name"] == "Maria"
        assert result[0]["payment_method"] == "cash"
        assert result[0]["notes"] == "Test client"

    def test_resolved_fields_are_canonical(self):
        raw = b"Surname,Given Name,Father Name,Passport Number,Travel Date\nX,Y,Z,PN123,2027-01-01\n"
        result = parse_csv(raw)
        row = result[0]
        assert list(row.keys()) == ["surname", "given_name", "father_name", "passport_number", "travel_date"]

    def test_raises_on_totally_unresolvable_headers(self):
        raw = b"Col1,Col2,Col3\nA,B,C\n"
        with pytest.raises(ValueError, match="No headers could be resolved"):
            parse_csv(raw)

    def test_parse_with_optional_fields_missing(self):
        raw = b"Surname,Given Name,Father Name,Nationality,Travel Date\nYann,Marie,Paul,France,2027-03-10\n"
        result = parse_csv(raw)
        assert result[0]["surname"] == "Yann"
        assert result[0]["nationality"] == "France"
        assert "mother_name" not in result[0]
        assert "date_of_birth" not in result[0]


class TestParseXlsx:
    @staticmethod
    def _make_xlsx(headers: list[str], rows: list[list]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        wb.close()
        return buf.getvalue()

    def test_parse_valid_xlsx(self):
        content = self._make_xlsx(
            ["Surname", "Given Name", "Passport Number", "Travel Date"],
            [["Smith", "John", "AB1234567", "2027-12-01"]],
        )
        result = parse_xlsx(content)
        assert len(result) == 1
        assert result[0]["surname"] == "Smith"
        assert result[0]["given_name"] == "John"

    def test_parse_french_headers(self):
        content = self._make_xlsx(
            ["Nom", "Prénom", "Date de naissance"],
            [["Dupont", "Jean", "1990-05-15"]],
        )
        result = parse_xlsx(content)
        assert result[0]["surname"] == "Dupont"
        assert result[0]["given_name"] == "Jean"
        assert result[0]["date_of_birth"] == "1990-05-15"

    def test_parse_arabic_headers(self):
        content = self._make_xlsx(
            ["اللقب", "الاسم", "تاريخ السفر"],
            [["محمد", "أحمد", "2027-06-15"]],
        )
        result = parse_xlsx(content)
        assert result[0]["surname"] == "محمد"
        assert result[0]["given_name"] == "أحمد"

    def test_empty_workbook_returns_empty_list(self):
        content = self._make_xlsx(["Surname"], [])
        result = parse_xlsx(content)
        assert result == []

    def test_header_only_returns_empty_list(self):
        content = self._make_xlsx(["Surname", "Given Name"], [])
        result = parse_xlsx(content)
        assert result == []

    def test_unknown_headers_silently_dropped(self):
        content = self._make_xlsx(
            ["Surname", "FooColumn", "Given Name"],
            [["Doe", "bar", "John"]],
        )
        result = parse_xlsx(content)
        assert len(result) == 1
        assert "foocolumn" not in result[0]
        assert result[0]["surname"] == "Doe"
        assert result[0]["given_name"] == "John"

    def test_raises_on_totally_unresolvable_headers(self):
        content = self._make_xlsx(["Col1", "Col2"], [["A", "B"]])
        with pytest.raises(ValueError, match="No headers could be resolved"):
            parse_xlsx(content)

    def test_integer_cells_converted_to_string(self):
        content = self._make_xlsx(
            ["Surname", "Passport Number"],
            [["Doe", 1234567]],
        )
        result = parse_xlsx(content)
        assert result[0]["passport_number"] == "1234567"

    def test_empty_cells_omitted(self):
        content = self._make_xlsx(
            ["Surname", "Given Name", "Mother Name"],
            [["Doe", "John", None]],
        )
        result = parse_xlsx(content)
        assert result[0]["surname"] == "Doe"
        assert result[0]["given_name"] == "John"
        assert "mother_name" not in result[0]

    def test_skip_empty_rows(self):
        content = self._make_xlsx(
            ["Surname", "Given Name"],
            [["Doe", "John"], [None, None]],
        )
        result = parse_xlsx(content)
        assert len(result) == 1
        assert result[0]["surname"] == "Doe"

    def test_multiple_data_rows(self):
        content = self._make_xlsx(
            ["Surname", "Given Name"],
            [["Doe", "John"], ["Smith", "Jane"]],
        )
        result = parse_xlsx(content)
        assert len(result) == 2
        assert result[0]["surname"] == "Doe"
        assert result[1]["given_name"] == "Jane"

    def test_mother_name_parent_name_fields(self):
        content = self._make_xlsx(
            ["Surname", "Given Name", "Father Name", "Mother Name"],
            [["Ali", "Ahmed", "Hassan", "Fatima"]],
        )
        result = parse_xlsx(content)
        assert result[0]["father_name"] == "Hassan"
        assert result[0]["mother_name"] == "Fatima"


class TestValidateRows:
    def _valid_row(self, **overrides) -> dict:
        row = {
            "surname": "Smith",
            "given_name": "John",
            "father_name": "Robert",
            "passport_number": "AB1234567",
            "nationality": "USA",
            "travel_type_id": "umrah",
            "travel_date": "2027-12-01",
        }
        row.update(overrides)
        return row

    def test_valid_row_no_errors(self):
        valid, errors = validate_rows([self._valid_row()])
        assert len(valid) == 1
        assert errors == []

    def test_missing_surname(self):
        valid, errors = validate_rows([self._valid_row(surname="")])
        assert len(valid) == 0
        assert any(e["field"] == "surname" for e in errors)

    def test_missing_given_name(self):
        valid, errors = validate_rows([self._valid_row(given_name="")])
        assert any(e["field"] == "given_name" for e in errors)

    def test_missing_father_name(self):
        valid, errors = validate_rows([self._valid_row(father_name="")])
        assert any(e["field"] == "father_name" for e in errors)

    def test_missing_passport_number(self):
        valid, errors = validate_rows([self._valid_row(passport_number="")])
        assert any(e["field"] == "passport_number" for e in errors)

    def test_missing_nationality(self):
        valid, errors = validate_rows([self._valid_row(nationality="")])
        assert any(e["field"] == "nationality" for e in errors)

    def test_missing_travel_type(self):
        valid, errors = validate_rows([self._valid_row(travel_type_id="")])
        assert any(e["field"] == "travel_type_id" for e in errors)

    def test_missing_travel_date(self):
        valid, errors = validate_rows([self._valid_row(travel_date="")])
        assert any(e["field"] == "travel_date" for e in errors)

    def test_invalid_date_format(self):
        valid, errors = validate_rows([self._valid_row(travel_date="not-a-date")])
        assert any("date" in e["message"].lower() for e in errors)

    def test_valid_date_formats(self):
        valid, errors = validate_rows([self._valid_row(travel_date="01/06/2027")])
        assert errors == []

    def test_valid_date_dd_mm_yyyy(self):
        valid, errors = validate_rows([self._valid_row(travel_date="15/03/2027")])
        assert errors == []

    def test_valid_date_mm_dd_yyyy(self):
        valid, errors = validate_rows([self._valid_row(travel_date="03/15/2027")])
        assert errors == []

    def test_invalid_gender(self):
        valid, errors = validate_rows([self._valid_row(gender="X")])
        assert any(e["field"] == "gender" for e in errors)

    def test_valid_gender_male(self):
        valid, errors = validate_rows([self._valid_row(gender="M")])
        assert errors == []

    def test_valid_gender_female(self):
        valid, errors = validate_rows([self._valid_row(gender="F")])
        assert errors == []

    def test_valid_gender_lowercase(self):
        valid, errors = validate_rows([self._valid_row(gender="m")])
        assert errors == []

    def test_gender_empty_is_ok(self):
        valid, errors = validate_rows([self._valid_row(gender="")])
        assert errors == []

    def test_optional_fields_empty_are_ok(self):
        row = self._valid_row(mother_name="", date_of_birth="", passport_issue_date="", passport_expiry="", payment_method="", notes="", gender="")
        valid, errors = validate_rows([row])
        assert errors == []

    def test_multiple_errors_in_one_row(self):
        valid, errors = validate_rows([self._valid_row(surname="", gender="X", travel_date="bad")])
        assert len(valid) == 0
        fields = {e["field"] for e in errors}
        assert "surname" in fields
        assert "gender" in fields
        assert "travel_date" in fields

    def test_mixed_valid_and_invalid_rows(self):
        rows = [
            self._valid_row(),
            self._valid_row(surname="", passport_number=""),
            self._valid_row(),
        ]
        valid, errors = validate_rows(rows)
        assert len(valid) == 2
        assert len(errors) >= 2

    def test_empty_row_list(self):
        valid, errors = validate_rows([])
        assert valid == []
        assert errors == []

    def test_error_has_row_index(self):
        valid, errors = validate_rows([
            self._valid_row(),
            self._valid_row(surname=""),
        ])
        assert errors[0]["row"] == 1  # second row (0-indexed)

    def test_error_has_field_and_message(self):
        valid, errors = validate_rows([self._valid_row(surname="")])
        e = errors[0]
        assert "row" in e
        assert "field" in e
        assert "message" in e
