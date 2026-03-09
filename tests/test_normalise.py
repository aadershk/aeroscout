"""Tests for core.normalise."""
from core.normalise import _norm, _valid_url, _is_nl, _parse_ct


class TestNorm:
    def test_camelcase(self):
        assert _norm("SeniorDataEngineer") == "Senior Data Engineer"

    def test_ats_code(self):
        assert _norm("I261217-002 SeniorDataEngineer") == "Senior Data Engineer"

    def test_bracket_prefix(self):
        assert _norm("[NL] Data Analyst") == "Data Analyst"

    def test_paren_prefix(self):
        assert _norm("(Remote) ML Engineer") == "ML Engineer"

    def test_html(self):
        assert _norm("<b>Data</b> Analyst") == "Data Analyst"

    def test_ats_code_dash(self):
        assert _norm("REQ-1234: Data Scientist") == "Data Scientist"

    def test_collapse_whitespace(self):
        assert _norm("Data   Analyst   Role") == "Data Analyst Role"

    def test_plain(self):
        assert _norm("Revenue Management Analyst") == "Revenue Management Analyst"

    def test_uppercase_split(self):
        # ABCDefg -> ABC Defg
        assert _norm("ABCDefg") == "ABC Defg"


class TestValidUrl:
    def test_valid_https(self):
        assert _valid_url("https://example.com/job/123") is True

    def test_valid_http(self):
        assert _valid_url("http://example.com") is True

    def test_javascript(self):
        assert _valid_url("javascript:void(0)") is False

    def test_hash(self):
        assert _valid_url("#") is False

    def test_empty(self):
        assert _valid_url("") is False

    def test_no_scheme(self):
        assert _valid_url("example.com/job") is False


class TestIsNl:
    def test_netherlands(self):
        assert _is_nl("Amsterdam, Netherlands") is True

    def test_schiphol(self):
        assert _is_nl("Schiphol") is True

    def test_nl_code(self):
        assert _is_nl("Location: NL") is True

    def test_foreign(self):
        assert _is_nl("London, UK") is False

    def test_utrecht(self):
        assert _is_nl("Utrecht") is True

    def test_noord_holland(self):
        assert _is_nl("Noord-Holland") is True


class TestParseCt:
    def test_with_charset(self):
        assert _parse_ct({"Content-Type": "text/html; charset=utf-8"}) == "text/html"

    def test_json(self):
        assert _parse_ct({"Content-Type": "application/json"}) == "application/json"

    def test_empty(self):
        assert _parse_ct({}) == ""
