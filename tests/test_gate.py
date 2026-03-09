"""Tests for core.gate — 25+ cases."""
from core.gate import passes_gate, _is_relevant


class TestGateRejects:
    def test_intern(self):
        ok, r = passes_gate("Data Science Intern")
        assert not ok and r == "intern/phd/thesis"

    def test_internship(self):
        ok, r = passes_gate("Data Internship")
        assert not ok and r == "intern/phd/thesis"

    def test_meewerkstage(self):
        ok, r = passes_gate("Meewerkstage Revenue Management")
        assert not ok and r == "intern/phd/thesis"

    def test_afstudeerstage(self):
        ok, r = passes_gate("Afstudeerstage Data Science")
        assert not ok and r == "intern/phd/thesis"

    def test_master_thesis(self):
        ok, r = passes_gate("Master Thesis: ML at NLR")
        assert not ok and r == "intern/phd/thesis"

    def test_phd(self):
        ok, r = passes_gate("PhD Data Scientist")
        assert not ok and r == "intern/phd/thesis"

    def test_pilot(self):
        ok, r = passes_gate("First Officer Boeing 737")
        assert not ok and r == "aviation_ops"

    def test_cabin_crew(self):
        ok, r = passes_gate("Cabin Crew Member")
        assert not ok and r == "aviation_ops"

    def test_aircraft_mechanic(self):
        ok, r = passes_gate("Aircraft Mechanic")
        assert not ok and r == "aviation_ops"

    def test_emc_engineer(self):
        ok, r = passes_gate("EMC Engineer")
        assert not ok and r == "hard_eng"

    def test_devops(self):
        ok, r = passes_gate("DevOps Engineer")
        assert not ok and r == "hard_eng"

    def test_sysadmin(self):
        ok, r = passes_gate("System Administrator")
        assert not ok and r == "hard_eng"

    def test_account_manager(self):
        ok, r = passes_gate("Account Manager")
        assert not ok and r == "hr_sales"

    def test_recruiter(self):
        ok, r = passes_gate("Recruiter")
        assert not ok and r == "hr_sales"

    def test_sales_manager(self):
        ok, r = passes_gate("Sales Manager")
        assert not ok and r == "hr_sales"

    def test_operations_manager_rejected(self):
        """Operations Manager → rejected by _MGMT_NOGO."""
        ok, r = passes_gate("Operations Manager")
        assert not ok and r == "mgmt_nogo"

    def test_office_manager_rejected(self):
        ok, r = passes_gate("Office Manager")
        assert not ok and r == "mgmt_nogo"

    def test_general_manager_rejected(self):
        ok, r = passes_gate("General Manager")
        assert not ok and r == "mgmt_nogo"

    def test_product_manager(self):
        ok, r = passes_gate("Product Manager Payments")
        assert not ok and r == "product_manager"

    def test_traineeship(self):
        ok, r = passes_gate("Traineeship Data Analytics")
        assert not ok and r == "traineeship"

    def test_bare_trainee(self):
        ok, r = passes_gate("Trainee")
        assert not ok and r == "bare_trainee"

    def test_dutch_required_desc(self):
        ok, r = passes_gate(
            "Data Analyst",
            description="We zoeken iemand met vloeiend Nederlands vereist voor deze functie",
        )
        assert not ok and r == "dutch_required"

    def test_dutch_must_speak(self):
        ok, r = passes_gate(
            "Data Analyst",
            description="You must speak Dutch fluently for this role",
        )
        assert not ok and r == "dutch_required"

    def test_senior_exp_desc(self):
        ok, r = passes_gate("Data Analyst", description="Requires 8 years of experience in analytics")
        assert not ok and r == "senior_exp"

    def test_staffing_company(self):
        ok, r = passes_gate("Data Analyst", company="Randstad")
        assert not ok and r == "staffing"


class TestGatePasses:
    def test_data_product_manager(self):
        ok, r = passes_gate("Data Product Manager")
        assert ok

    def test_trainee_analyst(self):
        ok, r = passes_gate("Trainee Analyst")
        assert ok

    def test_trainee_data_scientist(self):
        ok, r = passes_gate("Trainee Data Scientist")
        assert ok

    def test_data_analyst_trainee(self):
        """'Data Analyst Trainee' should pass (trainee with analyst)."""
        ok, r = passes_gate("Data Analyst Trainee")
        assert ok

    def test_revenue_manager_passes(self):
        """Revenue Manager → PASSES gate (scorer handles seniority)."""
        ok, r = passes_gate("Revenue Manager")
        assert ok

    def test_english_env(self):
        ok, r = passes_gate(
            "Data Analyst",
            description="Working language is English in an international team",
        )
        assert ok

    def test_dutch_desc_no_req(self):
        """Dutch description at NLR, NO Dutch required -> PASSES."""
        ok, r = passes_gate(
            "Data Analist",
            description="NLR zoekt een data analist voor ons team in Amsterdam. "
            "Je werkt met Python en SQL aan luchtvaart data projecten.",
            company="NLR",
        )
        assert ok

    def test_dutch_page_klm_no_req(self):
        """Dutch-language KLM page without Dutch requirement -> PASSES."""
        ok, r = passes_gate(
            "Business Analyst",
            description="KLM zoekt een business analyst voor het revenue team. "
            "Je analyseert data en werkt met Python.",
            company="KLM",
        )
        assert ok

    def test_revenue_mgmt_analyst(self):
        ok, r = passes_gate("Revenue Management Analyst")
        assert ok

    def test_business_analyst_aviation(self):
        """Business Analyst + aviation context -> PASSES."""
        ok, r = passes_gate(
            "Business Analyst",
            description="Aviation ground services analytics role",
        )
        assert ok

    def test_supply_chain_analyst(self):
        ok, r = passes_gate("Supply chain data- & process analyst")
        assert ok

    def test_dutch_nice_to_have(self):
        """'Nederlands is een pre' -> NOT rejected."""
        ok, r = passes_gate(
            "Data Analyst",
            description="Requirements: Python, SQL. Nederlands is een pre.",
        )
        assert ok

    def test_bij_voorkeur_dutch(self):
        """'bij voorkeur Nederlands' -> NOT rejected."""
        ok, r = passes_gate(
            "Data Analyst",
            description="Bij voorkeur spreek je Nederlands, maar het is geen vereiste.",
        )
        assert ok
