"""Tests for core/scorer.py."""
import pytest
from core.scorer import score, _company_tier


class TestCompanyTier:
    def test_klm_is_tier_a(self):
        s, label = _company_tier("KLM")
        assert label == "A"
        assert s == 45

    def test_amadeus_is_tier_a(self):
        s, label = _company_tier("Amadeus")
        assert label == "A"

    def test_deloitte_is_tier_b(self):
        s, label = _company_tier("Deloitte")
        assert label == "B"
        assert s == 30

    def test_asml_is_tier_c(self):
        s, label = _company_tier("ASML")
        assert label == "C"
        assert s == 15

    def test_catawiki_is_tier_d(self):
        s, label = _company_tier("Catawiki")
        assert label == "D"
        assert s == 8

    def test_unknown_company_zero(self):
        s, label = _company_tier("Some Random Corp")
        assert s == 0
        assert label == "?"


class TestScoringModel:
    def test_aviation_rm_role_scores_high(self):
        """A KLM revenue management role should score well above 80."""
        s, detail = score(
            title="Revenue Management Analyst",
            company="KLM",
            location="Amsterdam, Netherlands",
            description=(
                "Join our Revenue Management team at KLM airline. "
                "You will work on load factor optimisation, O&D demand forecasting, "
                "pricing strategies and fleet capacity planning. "
                "Python and SQL skills required. "
                "Our working language is English."
            ),
        )
        assert s >= 80, f"Expected >= 80, got {s}. Detail: {detail}"
        assert "title_t1" in detail
        assert "company_tier_A" in detail

    def test_chip_manufacturing_role_scores_low(self):
        """An NXP data analyst role with no aviation context should score lower."""
        s, detail = score(
            title="Data Analyst",
            company="NXP Semiconductors",
            location="Eindhoven, Netherlands",
            description=(
                "Analyse production line data for semiconductor manufacturing. "
                "SQL and Power BI experience required. "
                "Work closely with process engineers."
            ),
        )
        # Should get title_t2b + company_tier_C + NL location, but no aviation
        assert s < 80, f"Expected < 80, got {s}"
        assert "title_t2b" in detail
        assert "company_tier_C" in detail

    def test_dutch_required_penalty(self):
        s, detail = score(
            title="Data Analyst",
            company="Random Corp",
            location="Amsterdam",
            description="Vloeiend Nederlands is vereist voor deze functie.",
        )
        assert "dutch_required" in detail
        assert detail["dutch_required"] == -200

    def test_senior_title_penalty(self):
        s, detail = score(
            title="Senior Data Scientist",
            company="ING",
            location="Amsterdam, Netherlands",
            description="10+ years experience required.",
        )
        assert "senior_title" in detail
        assert detail["senior_title"] == -90

    def test_junior_signal_bonus(self):
        s, detail = score(
            title="Junior Data Analyst",
            company="Deloitte",
            location="Amsterdam, Netherlands",
            description="Entry-level position, 0-2 years experience.",
        )
        assert "junior_signal" in detail
        assert detail["junior_signal"] == 20

    def test_nl_location_missing_penalty(self):
        s, detail = score(
            title="Data Scientist",
            company="Databricks",
            location="London, UK",
            description="Based in London office.",
        )
        assert "location_unconfirmed" in detail
        assert detail["location_unconfirmed"] == -40

    def test_english_env_bonus(self):
        s, detail = score(
            title="Analytics Engineer",
            company="Catawiki",
            location="Amsterdam, Netherlands",
            description="Our working language is English. International team.",
        )
        assert "english_env" in detail
        assert detail["english_env"] == 15
