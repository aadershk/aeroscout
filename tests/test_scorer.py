"""Tests for core.scorer — 15+ cases."""
from core.scorer import _company_tier, score, infer_seniority


class TestCompanyTier:
    def test_ing_not_tier_a(self):
        """ING -> (15, 'C'), NOT (45, 'A')."""
        s, t = _company_tier("ING")
        assert (s, t) == (15, "C")

    def test_ing_bank(self):
        s, t = _company_tier("ING Bank")
        assert (s, t) == (15, "C")

    def test_booking(self):
        s, t = _company_tier("Booking.com")
        assert (s, t) == (45, "A")

    def test_ns_unknown(self):
        """NS alone should not match any tier."""
        s, t = _company_tier("NS")
        assert (s, t) == (0, "?")

    def test_ns_nederland(self):
        s, t = _company_tier("NS Nederland")
        assert (s, t) == (30, "B")

    def test_klm(self):
        s, t = _company_tier("KLM")
        assert (s, t) == (45, "A")

    def test_deloitte(self):
        s, t = _company_tier("Deloitte")
        assert (s, t) == (30, "B")

    def test_snowflake(self):
        s, t = _company_tier("Snowflake")
        assert (s, t) == (8, "D")

    def test_unknown(self):
        s, t = _company_tier("SomeRandomCompany")
        assert (s, t) == (0, "?")

    def test_dnata(self):
        s, t = _company_tier("dnata")
        assert (s, t) == (45, "A")


class TestScore:
    def test_revenue_mgmt_klm(self):
        """Revenue Management Analyst + KLM + NL + aviation desc -> score >= 100."""
        total, detail = score(
            "Revenue Management Analyst",
            "KLM",
            "Amsterdam, Netherlands",
            "Working with airline revenue management, yield optimization, "
            "fleet planning, demand forecasting. Python, SQL, Sabre GDS.",
        )
        assert total >= 100
        assert "title_t1" in detail
        assert "company_tier" in detail

    def test_business_analyst_dnata(self):
        """Business Analyst + dnata + aviation ground services -> score >= 55."""
        total, detail = score(
            "Business Analyst",
            "dnata",
            "Amsterdam, Netherlands",
            "Aviation ground services analytics role. Airport operations, "
            "airline handling, data analysis with Python and SQL.",
        )
        assert total >= 55
        assert "title_t2b" in detail

    def test_revenue_manager_hotel_overexp(self):
        """Revenue Manager + hotel + 3-4yr exp -> score < 40."""
        total, detail = score(
            "Revenue Manager",
            "Marriott Hotels",
            "Amsterdam",
            "Hotel revenue management role requiring 3-4 years of experience. "
            "Manage pricing strategy for 200-room property.",
        )
        assert total < 40
        assert detail.get("manager_title") == -50
        assert detail.get("overexp_3_4yr") == -30

    def test_analytics_engineer_transavia_no_loc_penalty(self):
        """Analytics Engineer + Transavia + no location -> NO no_nl penalty (tier A)."""
        total, detail = score(
            "Analytics Engineer",
            "Transavia",
            "",
            "Aviation analytics team",
        )
        assert "no_nl" not in detail

    def test_data_scientist_unknown_domain_mismatch(self):
        """Data Scientist + unknown co + no aviation + >100 char desc -> domain_mismatch."""
        total, detail = score(
            "Data Scientist",
            "RandomCo",
            "Amsterdam, Netherlands",
            "Building machine learning models for e-commerce recommendation systems. "
            "Work with Python, TensorFlow, and large-scale data pipelines. " * 2,
        )
        assert detail.get("domain_mismatch") == -25

    def test_data_scientist_unknown_empty_desc_no_mismatch(self):
        """Data Scientist + unknown co + empty desc -> NO domain_mismatch."""
        total, detail = score(
            "Data Scientist",
            "RandomCo",
            "Amsterdam, Netherlands",
            "",
        )
        assert "domain_mismatch" not in detail

    def test_overexp_5plus(self):
        """5+ years experience required -> overexp_5plus=-70."""
        total, detail = score(
            "Data Analyst",
            "Unknown Co",
            "Amsterdam",
            "5+ years experience required in data analytics and reporting.",
        )
        assert detail.get("overexp_5plus") == -70

    def test_junior_data_analyst_schiphol(self):
        """Junior Data Analyst + Schiphol -> junior_signal=+20."""
        total, detail = score(
            "Junior Data Analyst",
            "Schiphol Group",
            "Schiphol, Netherlands",
            "Entry level data analyst at Schiphol airport.",
        )
        assert detail.get("junior_signal") == 20
        assert detail.get("company_tier") == 45

    def test_senior_title_penalty(self):
        """Senior Data Scientist in title -> senior_title = -90."""
        total, detail = score(
            "Senior Data Scientist",
            "Booking.com",
            "Amsterdam",
            "Data science team working on pricing algorithms.",
        )
        assert detail.get("senior_title") == -90

    def test_tool_stack(self):
        total, detail = score(
            "Data Analyst",
            "Unknown Co",
            "Amsterdam",
            "Requirements: Python, SQL, Tableau, pandas",
        )
        assert "tool_stack" in detail

    def test_data_scientist_nxp_domain_mismatch(self):
        """Data Scientist + NXP + 0 aviation hits -> domain_mismatch = -25."""
        total, detail = score(
            "Data Scientist",
            "NXP Semiconductors",
            "Eindhoven, Netherlands",
            "Semiconductor manufacturing process optimization using ML. "
            "Working with Python, advanced statistics, and process data.",
        )
        assert detail.get("domain_mismatch") == -25


class TestSeniority:
    def test_senior(self):
        assert infer_seniority("Senior Data Scientist") == "Senior"

    def test_junior(self):
        assert infer_seniority("Junior Data Analyst") == "Junior"

    def test_medior(self):
        assert infer_seniority("Data Analyst") == "Medior"

    def test_junior_from_desc(self):
        assert infer_seniority("Data Analyst", "Entry-level position, 0-2 years") == "Junior"

    def test_manager_is_senior(self):
        assert infer_seniority("Revenue Manager") == "Senior"
