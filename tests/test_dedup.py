"""Tests for core/dedup.py."""
import pytest
from core.dedup import dedup
from core.models import Job


def make_job(title: str, company: str, url: str) -> Job:
    return Job(title=title, company=company, location="Amsterdam", url=url)


class TestDedup:
    def test_exact_url_dedup(self):
        jobs = [
            make_job("Data Analyst", "KLM", "https://klm.com/job/123"),
            make_job("Data Analyst", "KLM", "https://klm.com/job/123"),
        ]
        result = dedup(jobs)
        assert len(result) == 1

    def test_url_trailing_slash_dedup(self):
        jobs = [
            make_job("Data Analyst", "KLM", "https://klm.com/job/123"),
            make_job("Data Analyst", "KLM", "https://klm.com/job/123/"),
        ]
        result = dedup(jobs)
        assert len(result) == 1

    def test_uid_semantic_dedup(self):
        # Same title+company, different URLs → same uid → deduplicated
        jobs = [
            make_job("Revenue Management Analyst", "Amadeus", "https://amadeus.com/job/1"),
            make_job("Revenue Management Analyst", "Amadeus", "https://amadeus.com/job/2"),
        ]
        result = dedup(jobs)
        assert len(result) == 1

    def test_different_companies_not_deduped(self):
        jobs = [
            make_job("Data Scientist", "KLM", "https://klm.com/job/1"),
            make_job("Data Scientist", "Amadeus", "https://amadeus.com/job/1"),
        ]
        result = dedup(jobs)
        assert len(result) == 2

    def test_empty_list(self):
        assert dedup([]) == []

    def test_preserves_first_occurrence(self):
        jobs = [
            make_job("Data Analyst", "KLM", "https://klm.com/job/1"),
            make_job("Data Analyst", "KLM", "https://klm.com/job/2"),
        ]
        result = dedup(jobs)
        assert result[0].url == "https://klm.com/job/1"

    def test_url_case_insensitive(self):
        jobs = [
            make_job("Data Analyst", "KLM", "https://KLM.com/job/123"),
            make_job("Data Analyst", "KLM", "https://klm.com/job/123"),
        ]
        result = dedup(jobs)
        assert len(result) == 1
