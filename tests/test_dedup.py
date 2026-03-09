"""Tests for core.dedup."""
from core.dedup import dedup, _clean_url
from core.models import Job


class TestCleanUrl:
    def test_strip_utm(self):
        url = "https://example.com/job?utm_source=google&id=123"
        assert _clean_url(url) == "https://example.com/job?id=123"

    def test_strip_gclid(self):
        url = "https://example.com/job?gclid=abc123"
        assert _clean_url(url) == "https://example.com/job"

    def test_strip_fbclid(self):
        url = "https://example.com/job?fbclid=abc"
        assert _clean_url(url) == "https://example.com/job"

    def test_trailing_slash(self):
        assert _clean_url("https://example.com/job/") == "https://example.com/job"

    def test_lowercase(self):
        assert _clean_url("HTTPS://EXAMPLE.COM/Job") == "https://example.com/job"


class TestDedup:
    def test_url_dedup(self):
        j1 = Job("Data Analyst", "Co A", "NL", "https://example.com/job/1")
        j2 = Job("Data Analyst", "Co A", "NL", "https://example.com/job/1")
        assert len(dedup([j1, j2])) == 1

    def test_url_dedup_tracking(self):
        j1 = Job("Data Analyst", "Co A", "NL", "https://example.com/job/1")
        j2 = Job("Data Analyst", "Co A", "NL", "https://example.com/job/1?utm_source=google")
        assert len(dedup([j1, j2])) == 1

    def test_uid_dedup(self):
        j1 = Job("Data Analyst", "Co A", "NL", "https://a.com/1")
        j2 = Job("Data Analyst", "Co A", "NL", "https://b.com/2")
        # Same title+company → same uid
        assert j1.uid == j2.uid
        assert len(dedup([j1, j2])) == 1

    def test_different_jobs_kept(self):
        j1 = Job("Data Analyst", "Co A", "NL", "https://a.com/1")
        j2 = Job("Data Scientist", "Co B", "NL", "https://b.com/2")
        assert len(dedup([j1, j2])) == 2

    def test_keeps_first(self):
        j1 = Job("Data Analyst", "Co A", "NL", "https://a.com/1", source="first")
        j2 = Job("Data Analyst", "Co A", "NL", "https://b.com/2", source="second")
        result = dedup([j1, j2])
        assert result[0].source == "first"
