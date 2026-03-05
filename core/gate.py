"""Two-stage relevance gate for AeroScout.

Stage 1 — hard_reject(): discard titles that match exclusion rules regardless
           of company or description.
Stage 2 — is_relevant(): a job must have at least one data/analytics signal
           to pass through to scoring.
"""
from __future__ import annotations

import re

from core.normalise import _norm

# ---------------------------------------------------------------------------
# Stage 1: Hard-reject patterns (case-insensitive, full title check)
# ---------------------------------------------------------------------------

# Internship / student roles
_INTERN = re.compile(
    r"\b(intern(ship)?|stage|meewerkstage|afstudeerstage|student[\s\-]?assist|"
    r"werkstudent|traineeship|trainee|apprentice|bbl[\s\-]leerling)\b",
    re.I,
)

# Academic / research roles not targeted
_ACADEMIC = re.compile(
    r"\b(phd|ph\.d|doctoral|postdoc|post[\s\-]?doc|lecturer|professor|"
    r"researcher(?!\s+analyst))\b",
    re.I,
)

# Aviation operations non-analytics roles
_AVIATION_OPS = re.compile(
    r"\b(pilot|first officer|cabin crew|flight attendant|steward(ess)?|purser|"
    r"aircraft mechanic|avionics technician|ndt inspector|"
    r"line maintenance|aircraft engineer|aeronautical engineer|"
    r"structures engineer|composites engineer|wind tunnel engineer)\b",
    re.I,
)

# Engineering disciplines unrelated to analytics
_HARD_ENGINEERING = re.compile(
    r"\b(emc engineer|rf engineer|radar engineer|antenna engineer|"
    r"power electronics|embedded software engineer|firmware engineer|"
    r"sysadmin|system administrator|devops engineer|cloud engineer|"
    r"network engineer|security engineer|infrastructure engineer|"
    r"site reliability engineer|sre)\b",
    re.I,
)

# Non-data HR / recruitment
_HR_ROLES = re.compile(
    r"\b(recruiter|talent acquisition|hr (business partner|advisor|manager|generalist)|"
    r"human resources (manager|specialist)|payroll|compensation[\s&]+benefits)\b",
    re.I,
)

# Sales / commercial non-analytical
_SALES_ROLES = re.compile(
    r"\b(account manager|business development (manager|representative)|bdm|"
    r"sales (manager|representative|engineer|executive)|"
    r"customer success manager|field sales)\b",
    re.I,
)

# Product manager — allow "Data Product Manager"
_PM = re.compile(r"\bproduct manager\b", re.I)
_DATA_PM = re.compile(r"\bdata product manager\b", re.I)

# Dutch fluency required signals (in title or description)
_DUTCH_REQUIRED = re.compile(
    r"(vloeiend nederlands|moedertaal|native dutch|"
    r"c1[\s\-]?dutch|dutch[\s\-]?c1|"
    r"eis:.*\bnederlands\b|"
    r"beheers(t|ing) (de )?nederlandse taal|"
    r"uitstekende beheersing van het nederlands)",
    re.I,
)

# Temp / staffing agency signals (often in job title or description)
_STAFFING = re.compile(
    r"\b(hays|randstad|manpower|hinttech|fitura|adecco|yacht|"
    r"brunel|solvision|huxley|it-staffing|uitzendbureau|detachering(sbureau)?)\b",
    re.I,
)

# Senior / very experienced roles
_SENIOR_YEARS = re.compile(
    r"\b(10|[7-9])\+?\s*years?\s*(of\s*)?(experience|exp)\b"
    r"|minimum\s+[7-9]\s+years?"
    r"|\b(senior|principal|staff|distinguished|fellow)\s+(data scientist|"
    r"ml engineer|machine learning|analyst|engineer|scientist)\b",
    re.I,
)


def hard_reject(title: str, description: str = "", company: str = "") -> tuple[bool, str]:
    """Return (True, reason) if job must be discarded, else (False, '')."""
    t = _norm(title)
    combo = f"{t} {description[:400]}"  # limit desc scan for speed

    if _INTERN.search(t):
        return True, "internship/student role"
    if _ACADEMIC.search(t):
        return True, "academic/PhD role"
    if _AVIATION_OPS.search(t):
        return True, "aviation ops (non-analytics) role"
    if _HARD_ENGINEERING.search(t):
        return True, "hard engineering (non-data) role"
    if _HR_ROLES.search(t):
        return True, "HR/recruitment role"
    if _SALES_ROLES.search(t):
        return True, "sales/BDM role"
    if _PM.search(t) and not _DATA_PM.search(t):
        return True, "product manager (non-data)"
    if _DUTCH_REQUIRED.search(combo):
        return True, "Dutch fluency required"
    if _STAFFING.search(combo):
        return True, "temp/staffing agency"
    # Senior years check in description only (not title — "Senior" alone doesn't reject)
    if _SENIOR_YEARS.search(description[:600]):
        return True, "senior 7+ yrs experience required"

    return False, ""


# ---------------------------------------------------------------------------
# Stage 2: Relevance — must have at least one data/analytics signal
# ---------------------------------------------------------------------------

_RELEVANCE = re.compile(
    r"\b(data|analytics?|analyst|scientist|ml|machine learning|"
    r"revenue management|yield|pricing|forecasting|operations research|"
    r"optimis|quantitative|statistical|bi |business intelligence|"
    r"modelling|modeling|insight|intelligence|reporting|"
    r"aviation|airline|airport|cargo|fleet|schedule|network planning|"
    r"mro|maintenance operations|capacity|demand)\b",
    re.I,
)


def is_relevant(title: str, description: str = "") -> bool:
    """Return True if the job has at least one data/analytics signal."""
    t = _norm(title)
    return bool(_RELEVANCE.search(t) or _RELEVANCE.search(description[:300]))


def passes_gate(title: str, description: str = "", company: str = "") -> tuple[bool, str]:
    """Combined gate check. Returns (passes, reason_if_rejected)."""
    rejected, reason = hard_reject(title, description, company)
    if rejected:
        return False, reason
    if not is_relevant(title, description):
        return False, "no data/analytics signal"
    return True, ""
