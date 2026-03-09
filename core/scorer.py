"""Scoring engine for gated jobs."""
from __future__ import annotations

import re
from functools import lru_cache

from core.gate import _DUTCH_REQ, _STAFFING
from core.normalise import _is_nl

# -- Company tiers (word-boundary regex) ------------------------------------

def _make_pat(names: list[str]) -> re.Pattern:
    return re.compile(
        '|'.join(r'\b' + re.escape(n) + r'\b' for n in sorted(names, key=len, reverse=True)),
        re.I,
    )

TIER_A = _make_pat([
    "klm", "air france-klm", "transavia", "corendon", "tui fly",
    "amadeus", "sabre", "navitaire", "sita", "ibs software", "flyr labs", "flyr",
    "aviobook", "cirium", "oag", "navblue", "lufthansa systems",
    "schiphol group", "schiphol", "eurocontrol", "easa", "lvnl", "naco", "to70",
    "seabury consulting", "seabury", "aevean", "nlr",
    "aercap", "fokker services", "menzies aviation",
    "swissport", "dnata", "travix", "kiwi.com", "booking.com",
])
TIER_B = _make_pat([
    "mckinsey", "boston consulting group", "bcg", "bain", "oliver wyman",
    "roland berger", "kearney", "strategy&", "deloitte", "kpmg",
    "pricewaterhousecoopers", "pwc", "ernst & young", "accenture", "capgemini",
    "steer", "jacobs", "mott macdonald", "arcadis", "royal haskoningdhv",
    "goudappel", "wsp", "prorail", "port of rotterdam",
    "port of amsterdam", "dhl", "maersk", "dsv", "postnl", "kuehne+nagel",
    "expedia", "ns nederland",
])
TIER_C = _make_pat([
    "ing", "ing bank", "ing groep", "abn amro", "rabobank", "nn group", "aegon",
    "achmea", "asml", "philips", "shell", "nxp semiconductors",
    "wolters kluwer", "heineken", "adyen", "microsoft", "google", "amazon",
    "uber", "tomtom", "netflix",
])
TIER_D = _make_pat([
    "databricks", "snowflake", "palantir", "elastic", "spotify", "atlassian",
    "catawiki", "sendcloud", "bunq", "miro", "picnic", "bol.com", "coolblue",
])


@lru_cache(maxsize=512)
def _company_tier(company: str) -> tuple[int, str]:
    c = company.lower().strip()
    if TIER_A.search(c):
        return 45, "A"
    if TIER_B.search(c):
        return 30, "B"
    if TIER_C.search(c):
        return 15, "C"
    if TIER_D.search(c):
        return 8, "D"
    return 0, "?"


# -- Scoring signals --------------------------------------------------------

_ENGLISH_ENV = re.compile(
    r'working\s+language.*english|international\s+team'
    r'|dutch.*not\s+required',
    re.I,
)

_TITLE_T1 = re.compile(
    r'revenue\s+manag|yield\s+(?:anal|manag|optim)|pric(?:ing)?\s+anal|dynamic\s+pric'
    r'|fare\s+anal|operations?\s+research|\bor\s+(?:anal|sci)\b'
    r'|network\s+plann(?!.*plant)|(?:schedule|capacity|demand|fleet)\s+optim'
    r'|mro\s+(?:anal|data|engin)'
    r'|aviation\s+(?:anal|data|sci)|airline\s+(?:anal|data|pric)'
    r'|air\s+traffic\s+flow'
    r'|transport(?:ation)?\s+(?:econom|anal)|simulation\s+(?:anal|sci|engin)',
    re.I,
)

_TITLE_T2 = re.compile(
    r'data\s+scien|machine\s+learning\s+(?:engin|sci)'
    r'|\bml\b\s+(?:engin|sci)|\bai\b\s+(?:engin|sci)'
    r'|quantitative\s+(?:anal|resear)|decision\s+scien'
    r'|statistical\s+(?:anal|model)'
    r'|supply\s+chain\s+(?:data|anal)|logistics\s+(?:anal|data)'
    r'|management\s+consult|strategy\s+(?:anal|consult)'
    r'|forecasting\s+(?:anal|sci)',
    re.I,
)

_TITLE_T2B = re.compile(
    r'data\s+anal|analytics\s+engin'
    r'|\bbi\s+(?:anal|developer|engin)\b|business\s+intelli'
    r'|business\s+anal|operations?\s+anal'
    r'|process\s+anal|financial\s+anal|strategy\s+anal'
    r'|commercial\s+anal|insights\s+anal|performance\s+anal|reporting\s+anal',
    re.I,
)

_MANAGER_TITLE = re.compile(
    r'\bmanager\b(?!\s*(?:analyst|trainee|associate|programme))',
    re.I,
)

_OVEREXP_5PLUS = re.compile(
    r'\b[5-9]\+?\s*years?\s*(?:of\s*)?experience\b'
    r'|minimaal\s+[5-9]\s+jaar',
    re.I,
)

_OVEREXP_3_4YR = re.compile(
    r'\b[34]\+?\s*years?\s*(?:of\s*)?experience\b'
    r'|\bmedior\b(?!\s+of\s+senior)'
    r'|minimaal\s+[34]\s+jaar'
    r'|mid[\s-]senior',
    re.I,
)

_JUNIOR_SIGNAL = re.compile(
    r'\bjunior\b|\bjr\b|graduate|new\s+grad|entry[\s-]level|starter'
    r'|recently\s+graduated|early\s+career'
    r'|0-[23]\s+years'
    r'|MSc\s+graduate|MSc\s+preferred'
    r'|\bkickstart\b',
    re.I,
)

_SENIOR_TITLE = re.compile(
    r'\bsenior\b|\bsr\b|principal|staff\s+(?:data|engin)|lead\s+(?:data|engin)'
    r'|head\s+of|director|\bvp\b|vice\s+president|chief\s+(?:data|analytics)',
    re.I,
)

_AVIATION_CATEGORIES = [
    (re.compile(r'\bairline[s]?\b', re.I), "airline"),
    (re.compile(r'\bairport\b|\bschiphol\b|\blvnl\b|\beurocontrol\b', re.I), "airport"),
    (re.compile(r'revenue\s+m(?:gmt|anag)|yield\s+m(?:gmt|anag)', re.I), "revenue_mgmt"),
    (re.compile(r'\bfleet\b|\baircraft\b', re.I), "fleet"),
    (re.compile(r'\bcargo\b|\bfreight\b', re.I), "cargo"),
    (re.compile(r'\bmro\b|maintenance\s+repair', re.I), "mro"),
    (re.compile(r'\botp\b|load\s+factor|seat\s+factor', re.I), "ops_metrics"),
    (re.compile(r'\bo&d\b|\bitinerary\b', re.I), "od"),
    (re.compile(r'network\s+plann|schedule\s+optim', re.I), "network"),
    (re.compile(r'demand\s+forecast|capacity\s+plann', re.I), "demand"),
    (re.compile(r'amadeus|sabre|navitaire|\bsita\b|navblue', re.I), "tech_vendor"),
    (re.compile(r'disruption|\birops\b', re.I), "disruption"),
    (re.compile(r'\biata\b|\bicao\b|\beasa\b|\batc\b', re.I), "regulatory"),
    (re.compile(r'\bfares?\b|pricing\s+strategy|ancillary', re.I), "pricing"),
]

_TOOL_PATTERNS = [
    re.compile(r'\bpython\b', re.I),
    re.compile(r'\bsql\b', re.I),
    re.compile(r'scikit[\s-]?learn|\bsklearn\b', re.I),
    re.compile(r'\bxgboost\b|\blightgbm\b', re.I),
    re.compile(r'\bpandas\b|\bpolars\b|\bnumpy\b', re.I),
    re.compile(r'\bspark\b|\bpyspark\b|\bdatabricks\b', re.I),
    re.compile(r'\btableau\b|power\s+bi|\bqlik\b|\blooker\b', re.I),
    re.compile(r'\bcplex\b|\bgurobi\b|or[\s-]tools', re.I),
    re.compile(r'monte\s+carlo|\bbayesian\b', re.I),
    re.compile(r'\bdbt\b|\bairflow\b', re.I),
    re.compile(r'\btensorflow\b|\bpytorch\b', re.I),
    re.compile(r'\bmatlab\b', re.I),
]


def _count_aviation_hits(text: str) -> int:
    seen: set[str] = set()
    for pat, cat in _AVIATION_CATEGORIES:
        if cat not in seen and pat.search(text):
            seen.add(cat)
    return len(seen)


def _count_tools(text: str) -> int:
    return sum(1 for p in _TOOL_PATTERNS if p.search(text))


def infer_seniority(title: str, description: str = "") -> str:
    """Infer seniority level from title and description."""
    from core.normalise import _norm
    nt = _norm(title)
    if _SENIOR_TITLE.search(nt) or _MANAGER_TITLE.search(nt):
        return "Senior"
    if _JUNIOR_SIGNAL.search(nt):
        return "Junior"
    if description and _JUNIOR_SIGNAL.search(description[:400]):
        return "Junior"
    return "Medior"


def score(title: str, company: str, location: str, description: str) -> tuple[int, dict]:
    """Score a job. Returns (total, detail_dict)."""
    from core.normalise import _norm
    nt = _norm(title)
    detail: dict[str, int] = {}
    total = 0

    # dutch_req
    if description and _DUTCH_REQ.search(description[:2000]):
        detail["dutch_req"] = -200
        total -= 200

    # english_env
    if description and _ENGLISH_ENV.search(description[:2000]):
        detail["english_env"] = 15
        total += 15

    # title tiers
    if _TITLE_T1.search(nt):
        detail["title_t1"] = 55
        total += 55
    elif _TITLE_T2.search(nt):
        detail["title_t2"] = 30
        total += 30
    elif _TITLE_T2B.search(nt):
        detail["title_t2b"] = 20
        total += 20

    # desc_t1 — T1 in description but not in title
    if "title_t1" not in detail and description and _TITLE_T1.search(description[:800]):
        detail["desc_t1"] = 15
        total += 15

    # aviation_domain
    full_text = nt + " " + company + " " + description[:2000]
    av_hits = _count_aviation_hits(full_text)
    if av_hits > 0:
        av_score = min(av_hits * 8, 48)
        detail["aviation_domain"] = av_score
        total += av_score

    # tool_stack
    if description:
        tool_hits = _count_tools(description[:2000])
        if tool_hits > 0:
            ts = min(tool_hits * 4, 16)
            detail["tool_stack"] = ts
            total += ts

    # manager_title
    has_manager = False
    if _MANAGER_TITLE.search(nt):
        detail["manager_title"] = -50
        total -= 50
        has_manager = True

    # overexp_5plus
    if description and _OVEREXP_5PLUS.search(description[:800]):
        detail["overexp_5plus"] = -70
        total -= 70

    # overexp_3_4yr
    if description and _OVEREXP_3_4YR.search(description[:800]):
        detail["overexp_3_4yr"] = -30
        total -= 30

    # junior_signal
    junior_text = nt + " " + (description[:400] if description else "")
    if _JUNIOR_SIGNAL.search(junior_text):
        detail["junior_signal"] = 20
        total += 20

    # senior_title (title only, skip if manager_title already applied)
    if not has_manager and _SENIOR_TITLE.search(nt):
        detail["senior_title"] = -90
        total -= 90

    # company_tier
    tier_score, tier_label = _company_tier(company)
    if tier_score > 0:
        detail["company_tier"] = tier_score
        total += tier_score

    # no_nl penalty
    loc_desc = location + " " + (description[:300] if description else "")
    if not _is_nl(loc_desc) and tier_score < 30:
        detail["no_nl"] = -40
        total -= 40

    # staffing
    staffing_text = company + " " + (description[:300] if description else "")
    if _STAFFING.search(staffing_text):
        detail["staffing"] = -50
        total -= 50

    # domain_mismatch
    if tier_score < 30 and av_hits == 0 and len(description) > 100:
        detail["domain_mismatch"] = -25
        total -= 25

    return total, detail
