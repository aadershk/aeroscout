"""Tests for core/gate.py — 15 test cases covering all rejection rules."""
import pytest
from core.gate import hard_reject, is_relevant, passes_gate


# ── Hard reject rules ────────────────────────────────────────────────────────

class TestInternshipRejection:
    def test_intern_in_title(self):
        reject, reason = hard_reject("Data Science Intern")
        assert reject is True
        assert "internship" in reason

    def test_stage_in_title(self):
        reject, _ = hard_reject("Data Analyst Stage")
        assert reject is True

    def test_meewerkstage(self):
        reject, _ = hard_reject("Meewerkstage Data & Analytics")
        assert reject is True

    def test_afstudeerstage(self):
        reject, _ = hard_reject("Afstudeerstage Operations Research")
        assert reject is True

    def test_trainee_analyst_rejected(self):
        # "trainee analyst" is internship-like
        reject, _ = hard_reject("Trainee Analyst")
        assert reject is True


class TestAcademicRejection:
    def test_phd_rejected(self):
        reject, _ = hard_reject("PhD Researcher Data Science")
        assert reject is True

    def test_postdoc_rejected(self):
        reject, _ = hard_reject("Postdoc Machine Learning")
        assert reject is True


class TestAviationOpsRejection:
    def test_pilot_rejected(self):
        reject, _ = hard_reject("First Officer B737")
        assert reject is True

    def test_cabin_crew_rejected(self):
        reject, _ = hard_reject("Cabin Crew Member KLM")
        assert reject is True


class TestProductManagerRejection:
    def test_pm_rejected(self):
        reject, _ = hard_reject("Product Manager Payments")
        assert reject is True

    def test_data_pm_passes(self):
        reject, _ = hard_reject("Data Product Manager")
        assert reject is False


class TestDutchRequiredRejection:
    def test_dutch_in_description(self):
        reject, _ = hard_reject(
            "Data Analyst",
            description="Vereisten: vloeiend Nederlands, analytisch denkvermogen.",
        )
        assert reject is True

    def test_english_only_passes(self):
        reject, _ = hard_reject(
            "Data Analyst",
            description="Working language is English. Strong Python skills required.",
        )
        assert reject is False


class TestSalesRejection:
    def test_account_manager_rejected(self):
        reject, _ = hard_reject("Account Manager Enterprise Sales")
        assert reject is True

    def test_bdm_rejected(self):
        reject, _ = hard_reject("Business Development Manager EMEA")
        assert reject is True


# ── Relevance gate ───────────────────────────────────────────────────────────

class TestRelevance:
    def test_data_analyst_relevant(self):
        assert is_relevant("Data Analyst") is True

    def test_revenue_management_relevant(self):
        assert is_relevant("Revenue Management Analyst") is True

    def test_hr_manager_not_relevant(self):
        # HR manager with no data signal
        assert is_relevant("HR Manager") is False

    def test_description_can_make_relevant(self):
        assert is_relevant("Specialist", description="Experience with data analytics required") is True


# ── Combined gate ────────────────────────────────────────────────────────────

class TestPassesGate:
    def test_good_role_passes(self):
        ok, reason = passes_gate("Revenue Management Analyst", company="KLM")
        assert ok is True
        assert reason == ""

    def test_intern_rejected(self):
        ok, reason = passes_gate("Data Science Intern", company="Amadeus")
        assert ok is False
        assert reason != ""

    def test_no_signal_rejected(self):
        ok, _ = passes_gate("Office Manager", description="Manages office supplies")
        assert ok is False
