import pytest
from app.services.import_parser import HEADER_ALIASES, resolve_field


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
