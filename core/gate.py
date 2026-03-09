"""Two-stage gate: hard_reject + is_relevant."""
from __future__ import annotations

import re

from core.normalise import _norm

# ── Stage 1: Hard reject patterns ──────────────────────────────────────────

_INTERN = re.compile(
    r'\binter[nm](?:ship)?\b|meewerkstage|afstudeerstage|afstudeer[\s-]?stage'
    r'|werkstudent|student[\s-]?(?:assist|worker)'
    r'|\bbbL[\s-]?leerling\b|\bapprentice\b|\bph\s*d\b|ph\.d|doctoral|postdoc'
    r'|master[\s-]?thesis|graduation[\s-]?project|afstudeer[\s-]?project',
    re.I,
)

_TRAINEE_REJECT = re.compile(r'\btraineeship\b', re.I)
_TRAINEE_BARE = re.compile(r'\btrainee\b', re.I)
_TRAINEE_PASS = re.compile(
    r'\btrainee\s+(?:analyst|scientist|consultant|data)\b'
    r'|\b(?:analyst|scientist|consultant|data)\s+trainee\b',
    re.I,
)

_AVIATION_OPS = re.compile(
    r'pilot(?!\s+(?:data|project))|first\s+officer|co[\s-]?pilot'
    r'|cabin\s+crew|flight\s+attendant|steward(?:ess)?|purser|gezagvoerder'
    r'|aircraft\s+mechanic|vliegtuig(?:monteur|technicus)'
    r'|avionics\s+tech|ndt\s+inspector|borescope|engine\s+test\s+cell'
    r'|line\s+maintenance\s+tech(?!\s+data)'
    r'|structures?\s+engineer(?!\s+data)|composites?\s+engineer'
    r'|wind\s+tunnel(?!\s+data)',
    re.I,
)

_HARD_ENG = re.compile(
    r'emc\s+engineer|rf\s+(?:engineer|specialist)(?!\s+data)'
    r'|radar\s+engineer|antenna\s+engineer'
    r'|embedded\s+(?:software|systems?)\s+engineer|firmware\s+engineer'
    r'|sysadmin|system\s+administrator'
    r'|dev\s*ops\s+engineer(?!\s+(?:data|ml))'
    r'|cloud\s+engineer(?!\s+(?:data|analytics))'
    r'|network\s+engineer(?!\s+(?:data|planning))'
    r'|security\s+engineer(?!\s+data)'
    r'|infrastructure\s+engineer(?!\s+data)'
    r'|\bsre\b(?!\s+data)',
    re.I,
)

_HR_SALES = re.compile(
    r'recruiter(?!\s+data)|talent\s+acquisition'
    r'|account\s+manager(?!\s+(?:data|analytics))'
    r'|business\s+development\s+(?:manager|rep|exec)(?!\s+data)'
    r'|\bbdm\b(?!\s+data)'
    r'|sales\s+(?:manager|rep|exec|engineer)(?!\s+(?:data|analytics))'
    r'|customer\s+success\s+manager(?!\s+(?:data|analytics))'
    r'|field\s+sales',
    re.I,
)

_MGMT_NOGO = re.compile(
    r'\b(?:operations?\s+manager|general\s+manager|station\s+manager'
    r'|floor\s+manager|branch\s+manager|country\s+manager'
    r'|regional\s+manager|area\s+manager|office\s+manager'
    r'|facilities\s+manager)\b',
    re.I,
)

_PM = re.compile(r'\bproduct\s+manager\b', re.I)
_PM_DATA = re.compile(r'\bdata\s+product\s+manager\b', re.I)

_SENIOR_EXP = re.compile(
    r'\b(?:10|[7-9])\+?\s*years?\s*(?:of\s*)?(?:relevant\s*)?experience\b'
    r'|minimum\s+[7-9]\s+years?|at\s+least\s+[7-9]\s+years?'
    r'|\bminimaal\s+[7-9]\s+jaar\b',
    re.I,
)

_STAFFING = re.compile(
    r'hays|randstad|manpower|adecco|\byacht\b|brunel|hinttech|fitura'
    r'|gi[\s-]?group|vedior|uitzendbureau|detachering(?:sbureau)?'
    r'|werving\s+en\s+selectie',
    re.I,
)

_DUTCH_REQ = re.compile(
    r"""
    vloeiend\s+(?:in\s+)?(?:de\s+)?nederlands(?:e\s+taal)?
  | beheersing\s+van\s+(?:de\s+)?(?:nederlandse\s+)?taal(?:\s+is\s+vereist)?
  | uitstekende\s+beheersing\s+van\s+het\s+nederlands
  | moedertaal\s+(?:is\s+)?nederlands
  | native\s+dutch\s+speaker
  | dutch\s+(?:language\s+)?(?:is\s+)?(?:mandatory|required|essential|a\s+must)
  | must\s+(?:speak|be\s+fluent\s+in)\s+dutch
  | c1[\s-]?(?:level\s+)?dutch|dutch[\s-]?c1
  | eis(?:t|en)?:?\s+.*?\bnederlands\b
  | vereiste?:?\s+.*?\bnederlands\b
  | je\s+(?:spreekt|beheerst)\s+(?:vloeiend\s+)?(?:de\s+)?nederlandse
""",
    re.I | re.X,
)

# ── Stage 2: Relevance ────────────────────────────────────────────────────

_RELEVANCE = re.compile(
    r"""
    \bdata\s+(?:scien|anal(?!og)|engin|manag)
  | analytics?\s+engin
  | \bbi\s+(?:anal|developer|engin)\b | business\s+intelli
  | \bbusiness\s+anal(?:yst)?\b | \boperations?\s+anal(?:yst)?\b
  | \bprocess\s+anal(?:yst)?\b | \bfinancial\s+anal(?:yst)?\b
  | \bstrategy\s+anal(?:yst)?\b | \bcommercial\s+anal
  | revenue\s+manag | yield\s+(?:anal|manag|optim) | pric(?:ing)?\s+anal
  | operations?\s+research | \bor\s+(?:anal|sci)\b
  | network\s+plann(?!.*plant) | schedule\s+optim | capacity\s+(?:plann|anal)
  | demand\s+(?:forecast|plann) | fleet\s+optim
  | mro\s+(?:anal|data|engin) | aviation\s+(?:anal|data|consult)
  | machine\s+learning | \bml\s+(?:engin|sci|anal)\b | \bai\s+(?:engin|sci|anal)\b
  | quantitative\s+(?:anal|resear) | decision\s+scien | statistical\s+(?:anal|model)
  | management\s+consult | supply\s+chain\s+(?:data|anal)
  | logistics\s+(?:anal|data) | transport(?:ation)?\s+(?:anal|econom)
  | simulation\s+(?:anal|sci|engin)
  | \banalyst\b
  | (?:data|analyse)\s+(?:specialist|analist) | analist\s+(?:data|business|operations?)
  | data\s+product\s+manag
  | \bscientist\b(?!\s*[\s-]+(?:dron|propuls|wind|laser|rf|radar))
""",
    re.I | re.X,
)


def _is_relevant(title: str, description: str = "") -> bool:
    """Check if a title (or fallback description) matches relevance patterns."""
    norm_title = _norm(title)
    if _RELEVANCE.search(norm_title):
        return True
    if description and _RELEVANCE.search(description[:400]):
        return True
    return False


def passes_gate(title: str, description: str = "", company: str = "") -> tuple[bool, str]:
    """Two-stage gate. Returns (pass, reason)."""
    norm_title = _norm(title)
    combo = norm_title + " " + description[:500]

    # ── Stage 1: Hard reject ───────────────────────────────────────────
    # Intern/PhD/thesis
    if _INTERN.search(norm_title):
        return False, "intern/phd/thesis"

    # Trainee logic
    if _TRAINEE_REJECT.search(norm_title):
        return False, "traineeship"
    if _TRAINEE_BARE.search(norm_title) and not _TRAINEE_PASS.search(norm_title):
        return False, "bare_trainee"

    # Aviation ops
    if _AVIATION_OPS.search(norm_title):
        return False, "aviation_ops"

    # Hard engineering
    if _HARD_ENG.search(norm_title):
        return False, "hard_eng"

    # HR/Sales
    if _HR_SALES.search(norm_title):
        return False, "hr_sales"

    # Non-data management
    if _MGMT_NOGO.search(norm_title):
        return False, "mgmt_nogo"

    # Product Manager (not Data Product Manager)
    if _PM.search(norm_title) and not _PM_DATA.search(norm_title):
        return False, "product_manager"

    # Senior experience (description only)
    if description and _SENIOR_EXP.search(description[:600]):
        return False, "senior_exp"

    # Staffing agencies
    staffing_text = company + " " + description[:300]
    if _STAFFING.search(staffing_text):
        return False, "staffing"

    # Dutch language required (description only)
    if description and _DUTCH_REQ.search(description[:2000]):
        return False, "dutch_required"

    # ── Stage 2: Relevance ─────────────────────────────────────────────
    if not _is_relevant(norm_title, description):
        return False, "not_relevant"

    return True, "pass"
