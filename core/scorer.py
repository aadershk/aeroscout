"""Aviation-first scoring model for AeroScout.

Score components (additive):
  Dutch required          → -200
  English env detected    → +15
  Title T1 (RM/OR/MRO)   → +55
  Title T2 (DS/ML/consult)→ +30
  Title T2b (DA/BI/eng)   → +20
  Desc T1 hits            → +15
  Aviation domain hits    → +8 each, max +48
  Tool stack hits         → +4 each, max +16
  Junior/graduate signal  → +20
  Senior signal in title  → -90
  Company tier A/B/C/D    → +45/+30/+15/+8
  NL location unconfirmed → -40
  Temp/staffing agency    → -50
  Domain mismatch         → -25  (non-aviation co + 0 aviation desc hits)
"""
from __future__ import annotations

import re
from typing import Any

from core.normalise import _norm

# ---------------------------------------------------------------------------
# Title tier patterns
# ---------------------------------------------------------------------------

_T1 = re.compile(
    r"\b(revenue management|yield management|yield analyst|"
    r"pricing analyst|airline pricing|fare analyst|"
    r"operations research|or analyst|or scientist|"
    r"network planning|schedule optimi|capacity planning|"
    r"demand forecast|mro analytics|mro engineer|fleet optimi|"
    r"commercial analyst|aviation data|aviation analytics)\b",
    re.I,
)

_T2 = re.compile(
    r"\b(data scientist|machine learning engineer|ml engineer|"
    r"quantitative analyst|quant analyst|decision scientist|"
    r"supply chain data|logistics analytics|transport econom|"
    r"management consultant|simulation analyst|statistical (analyst|model))\b",
    re.I,
)

_T2B = re.compile(
    r"\b(data analyst|analytics engineer|bi analyst|bi developer|"
    r"business intelligence|data engineer|insights analyst|"
    r"performance analyst|commercial analytics|reporting analyst)\b",
    re.I,
)

# ---------------------------------------------------------------------------
# Seniority signals
# ---------------------------------------------------------------------------

_SENIOR_TITLE = re.compile(
    r"\b(senior|sr\.|principal|staff|lead|head of|director|vp |vice president|"
    r"chief data|cdo|cto|manager(?! analyst))\b",
    re.I,
)

_JUNIOR = re.compile(
    r"\b(junior|jr\.|graduate|entry[\s\-]?level|associate analyst|"
    r"starting|starter|fresh|trainee analyst|early career|"
    r"0[\s\-]?2\s*years?|1[\s\-]?2\s*years?)\b",
    re.I,
)

# ---------------------------------------------------------------------------
# Company tiers — exact company name matching
# ---------------------------------------------------------------------------

_TIER_A = {
    "klm", "air france-klm", "air france klm", "transavia", "corendon",
    "tui fly", "tui fly nl", "amadeus", "sabre", "navitaire", "sita",
    "ibs software", "flyr labs", "flyr", "aviobook", "cirium", "oag",
    "navblue", "lufthansa systems", "schiphol", "schiphol group",
    "eurocontrol", "easa", "lvnl", "naco", "to70", "seabury",
    "seabury consulting", "aevean", "nlr", "aercap", "fokker services",
    "menzies aviation", "swissport", "dnata", "travix", "kiwi.com",
    "booking.com",
}

_TIER_B = {
    "mckinsey", "bcg", "boston consulting", "bain", "oliver wyman",
    "roland berger", "kearney", "strategy&", "deloitte", "kpmg", "pwc",
    "pricewaterhousecoopers", "ey", "ernst & young", "accenture", "capgemini",
    "ibm", "steer", "jacobs", "mott macdonald", "arcadis",
    "royal haskoningdhv", "goudappel", "ns", "prorail",
    "port of rotterdam", "port of amsterdam", "lvnl", "dhl", "maersk",
    "dsv", "postnl", "kuehne+nagel", "kuehne nagel",
}

_TIER_C = {
    "ing", "abn amro", "rabobank", "nn group", "aegon", "achmea",
    "asml", "philips", "shell", "nxp", "wolters kluwer", "heineken",
    "adyen", "microsoft", "google", "amazon", "uber", "tomtom",
}

_TIER_D = {
    "databricks", "snowflake", "palantir", "elastic", "spotify",
    "atlassian", "catawiki", "sendcloud", "bunq", "miro", "picnic",
    "bol.com", "coolblue",
}


def _company_tier(company: str) -> tuple[int, str]:
    """Return (score_delta, tier_label) for a company name."""
    c = company.lower().strip()
    # Partial match for company names with suffixes
    for name in _TIER_A:
        if name in c or c in name:
            return 45, "A"
    for name in _TIER_B:
        if name in c or c in name:
            return 30, "B"
    for name in _TIER_C:
        if name in c or c in name:
            return 15, "C"
    for name in _TIER_D:
        if name in c or c in name:
            return 8, "D"
    return 0, "?"

# ---------------------------------------------------------------------------
# Domain signals (for description scanning)
# ---------------------------------------------------------------------------

_AVIATION_SIGNALS = [
    re.compile(p, re.I) for p in [
        r"\b(airline|airlines)\b",
        r"\b(airport|schiphol)\b",
        r"\b(revenue management|yield management)\b",
        r"\b(fleet|aircraft)\b",
        r"\b(cargo|freight)\b",
        r"\b(mro|maintenance repair)\b",
        r"\b(otp|on[\s\-]?time performance)\b",
        r"\b(load factor|seat factor)\b",
        r"\b(o&d|origin.?destination)\b",
        r"\b(network planning|schedule optimi)\b",
    ]
]

_TOOL_SIGNALS = [
    re.compile(p, re.I) for p in [
        r"\bpython\b",
        r"\bsql\b",
        r"\b(scikit[\s\-]?learn|sklearn)\b",
        r"\b(xgboost|lightgbm)\b",
        r"\b(pandas|numpy|polars)\b",
        r"\b(spark|databricks)\b",
        r"\b(tableau|power bi|looker)\b",
        r"\bmatlab\b",
    ]
]

_DUTCH_REQUIRED_DESC = re.compile(
    r"(vloeiend nederlands|moedertaal|native dutch|"
    r"c1[\s\-]?dutch|dutch[\s\-]?c1|"
    r"beheers(t|ing).{0,20}nederlandse|"
    r"uitstekende beheersing van het nederlands)",
    re.I,
)

_ENGLISH_ENV = re.compile(
    r"\b(working language.{0,20}english|"
    r"english.{0,20}working language|"
    r"international (team|environment|company)|"
    r"our language is english|"
    r"english[\s\-]speaking (team|environment))\b",
    re.I,
)

_NL_LOCATION = re.compile(
    r"\b(netherlands|amsterdam|schiphol|eindhoven|rotterdam|"
    r"den haag|the hague|utrecht|leiden|haarlem|delft|"
    r"\bnl\b)\b",
    re.I,
)

_STAFFING = re.compile(
    r"\b(hays|randstad|manpower|hinttech|fitura|adecco|yacht|"
    r"brunel|solvision|huxley)\b",
    re.I,
)

_AVIATION_COMPANIES = _TIER_A  # alias — aviation ecosystem = tier A set


def score(
    title: str,
    company: str,
    location: str,
    description: str = "",
) -> tuple[int, dict[str, Any]]:
    """Compute relevance score and return (total, detail_dict)."""
    t = _norm(title)
    desc = description[:2000]  # cap for speed
    detail: dict[str, Any] = {}
    total = 0

    # --- Language signals ---
    if _DUTCH_REQUIRED_DESC.search(desc):
        total -= 200
        detail["dutch_required"] = -200
    if _ENGLISH_ENV.search(desc):
        total += 15
        detail["english_env"] = +15

    # --- Title tier ---
    if _T1.search(t):
        total += 55
        detail["title_t1"] = +55
    elif _T2.search(t):
        total += 30
        detail["title_t2"] = +30
    elif _T2B.search(t):
        total += 20
        detail["title_t2b"] = +20

    # --- Description T1 hit ---
    if _T1.search(desc) and "title_t1" not in detail:
        total += 15
        detail["desc_t1_hit"] = +15

    # --- Aviation domain hits (description) ---
    av_hits = sum(1 for p in _AVIATION_SIGNALS if p.search(desc))
    av_score = min(av_hits * 8, 48)
    if av_score:
        total += av_score
        detail["aviation_domain"] = av_score

    # --- Tool stack hits ---
    tool_hits = sum(1 for p in _TOOL_SIGNALS if p.search(desc))
    tool_score = min(tool_hits * 4, 16)
    if tool_score:
        total += tool_score
        detail["tool_stack"] = tool_score

    # --- Seniority ---
    if _JUNIOR.search(t) or _JUNIOR.search(desc[:400]):
        total += 20
        detail["junior_signal"] = +20
    if _SENIOR_TITLE.search(t):
        total -= 90
        detail["senior_title"] = -90

    # --- Company tier ---
    tier_score, tier_label = _company_tier(company)
    if tier_score:
        total += tier_score
        detail[f"company_tier_{tier_label}"] = tier_score

    # --- Location check ---
    loc_text = f"{location} {desc[:300]}"
    if not _NL_LOCATION.search(loc_text):
        total -= 40
        detail["location_unconfirmed"] = -40

    # --- Staffing agency ---
    if _STAFFING.search(f"{company} {desc[:200]}"):
        total -= 50
        detail["staffing_agency"] = -50

    # --- Domain mismatch: non-aviation company with zero aviation desc hits ---
    c_lower = company.lower()
    is_aviation_co = any(name in c_lower for name in _AVIATION_COMPANIES)
    if not is_aviation_co and av_hits == 0 and tier_score < 30:
        total -= 25
        detail["domain_mismatch"] = -25

    detail["total"] = total
    return total, detail
