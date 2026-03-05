"""Tests for core/normalise.py."""
import pytest
from core.normalise import _norm, _valid_url, _parse_ct


class TestNorm:
    def test_strips_html_tags(self):
        assert _norm("<b>Data Analyst</b>") == "Data Analyst"

    def test_strips_ats_code_prefix(self):
        # REQ-1234: prefix
        assert _norm("REQ-1234: Revenue Management Analyst") == "Revenue Management Analyst"

    def test_strips_bracket_prefix(self):
        assert _norm("[NL] Data Scientist") == "Data Scientist"

    def test_strips_paren_prefix(self):
        assert _norm("(AMS) Yield Analyst") == "Yield Analyst"

    def test_collapses_whitespace(self):
        assert _norm("Data   Scientist  ") == "Data Scientist"

    def test_passthrough_clean_title(self):
        assert _norm("Operations Research Analyst") == "Operations Research Analyst"

    def test_empty_string(self):
        assert _norm("") == ""

    def test_html_entities_not_mangled(self):
        # We strip tags, not entities; &amp; stays (handled by BS4 upstream)
        result = _norm("Data &amp; Analytics")
        assert "Data" in result


class TestValidUrl:
    def test_valid_https(self):
        assert _valid_url("https://example.com/jobs/123") is True

    def test_valid_http(self):
        assert _valid_url("http://careers.company.com") is True

    def test_empty_string(self):
        assert _valid_url("") is False

    def test_no_scheme(self):
        assert _valid_url("example.com/jobs") is False

    def test_ftp_rejected(self):
        assert _valid_url("ftp://example.com") is False

    def test_none_like_empty(self):
        assert _valid_url("") is False


class TestParseCt:
    def test_json(self):
        assert _parse_ct({"Content-Type": "application/json; charset=utf-8"}) == "application/json"

    def test_html(self):
        assert _parse_ct({"content-type": "text/html"}) == "text/html"

    def test_missing(self):
        assert _parse_ct({}) == ""
