"""
Rule-based scoring for jobs and leads. No Claude API calls needed — fast and free.
"""

from src.db import score_label

# ── Job Scorer ────────────────────────────────────────────────────────────────

_JOB_SKILL_KEYWORDS = [
    ("project management", 10), ("delivery", 8), ("program manager", 9),
    ("software engineer", 10), ("fullstack", 10), ("full stack", 10), ("full-stack", 10),
    ("frontend", 8), ("backend", 8), ("react", 7), ("node", 6),
    ("aem", 9), ("adobe experience", 9),
    ("ai engineer", 10), ("machine learning", 7), ("llm", 8), ("ai/ml", 9),
    ("product manager", 9), ("product owner", 8), ("product lead", 9),
    ("solution architect", 10), ("solutions architect", 10), ("tech lead", 9),
    ("technical lead", 9), ("engineering manager", 8), ("scrum master", 6),
    ("typescript", 7), ("javascript", 7), ("python", 7),
]

_REMOTE_KEYWORDS = ["remote", "work from home", "wfh", "anywhere", "distributed"]
_LATAM_FRIENDLY = ["latam", "latin america", "colombia", "bogota", "medellín", "south america"]
_SENIORITY_SENIOR = ["senior", "lead", "principal", "staff", "head of", "director", "vp ", "chief"]
_SENIORITY_MID = ["mid", "intermediate", "iii", " ii "]
_SENIORITY_JUNIOR = ["junior", "entry", "associate", " i ", "intern"]

_GOOD_INDUSTRIES = [
    "technology", "software", "saas", "fintech", "healthtech", "edtech",
    "consulting", "digital agency", "e-commerce", "ai", "platform",
]
_BAD_INDUSTRIES = ["oil", "tobacco", "gambling", "mining", "fast food"]


class JobScorer:
    """
    Scores a job on a 0–100 scale.

    Input dict expected keys (same as CSV columns):
        Job Title, Company Name, Location, job_description (optional)
    """

    def score(self, job: dict) -> dict:
        # Accept both CSV column names ("Job Title") and DB column names ("title")
        title = (job.get("Job Title") or job.get("title") or "").lower()
        company = (job.get("Company Name") or job.get("company") or "").lower()
        location = (job.get("Location") or job.get("location") or "").lower()
        description = (job.get("job_description") or "").lower()
        full_text = f"{title} {company} {location} {description}"

        skill_pts, skill_reasons = self._score_skills(title, description)
        remote_pts, remote_reason = self._score_remote(location, description)
        seniority_pts, seniority_reason = self._score_seniority(title)
        industry_pts, industry_reason = self._score_industry(company, description)
        latam_pts, latam_reason = self._score_latam(location, description)

        total = min(100, skill_pts + remote_pts + seniority_pts + industry_pts + latam_pts)
        label = score_label(total)

        reasons = [r for r in [skill_reasons, remote_reason, seniority_reason, industry_reason, latam_reason] if r]

        return {
            "job_score": total,
            "skill_match_score": skill_pts,
            "score_label": label,
            "reasons": reasons,
            "breakdown": {
                "skills": skill_pts,
                "remote": remote_pts,
                "seniority": seniority_pts,
                "industry": industry_pts,
                "latam_friendly": latam_pts,
            },
        }

    def _score_skills(self, title: str, description: str) -> tuple:
        text = f"{title} {description}"
        pts = 0
        matched = []
        for kw, weight in _JOB_SKILL_KEYWORDS:
            if kw in text:
                pts += weight
                matched.append(kw)
        pts = min(50, pts)
        reason = f"Skills matched: {', '.join(matched[:4])}" if matched else ""
        return pts, reason

    def _score_remote(self, location: str, description: str) -> tuple:
        text = f"{location} {description}"
        for kw in _REMOTE_KEYWORDS:
            if kw in text:
                return 20, "Remote-friendly"
        return 0, ""

    def _score_seniority(self, title: str) -> tuple:
        for kw in _SENIORITY_SENIOR:
            if kw in title:
                return 15, f"Senior-level role ({kw})"
        for kw in _SENIORITY_MID:
            if kw in title:
                return 8, "Mid-level role"
        for kw in _SENIORITY_JUNIOR:
            if kw in title:
                return -5, "Junior-level (deprioritized)"
        return 10, "Seniority level unclear (neutral)"

    def _score_industry(self, company: str, description: str) -> tuple:
        text = f"{company} {description}"
        for kw in _BAD_INDUSTRIES:
            if kw in text:
                return -10, f"Industry mismatch ({kw})"
        for kw in _GOOD_INDUSTRIES:
            if kw in text:
                return 10, f"Good industry fit ({kw})"
        return 5, ""

    def _score_latam(self, location: str, description: str) -> tuple:
        text = f"{location} {description}"
        for kw in _LATAM_FRIENDLY:
            if kw in text:
                return 10, "LATAM-friendly role"
        if any(kw in text for kw in _REMOTE_KEYWORDS):
            return 5, "Remote (likely open to LATAM)"
        return 0, ""


# ── Lead Scorer ───────────────────────────────────────────────────────────────

_TARGET_INDUSTRIES = [
    ("real estate", 15), ("property", 12), ("mortgage", 10),
    ("professional services", 12), ("consulting", 10), ("law firm", 12), ("legal", 10),
    ("restaurant", 10), ("hospitality", 8), ("food", 7),
    ("startup", 12), ("saas", 12), ("tech", 10),
    ("ecommerce", 12), ("retail", 8),
    ("healthcare", 10), ("clinic", 10), ("dental", 10),
    ("local business", 10), ("smb", 10), ("small business", 10),
]

_PAIN_SIGNAL_KEYWORDS = [
    ("manual process", 15), ("spreadsheet", 12), ("no crm", 15), ("growing team", 10),
    ("hiring", 8), ("expansion", 10), ("new office", 10), ("scale", 8),
    ("outdated website", 12), ("no automation", 15), ("inefficient", 10),
    ("crm implementation", 14), ("digital transformation", 12),
]

_CONTACT_ROLES_GOOD = [
    "cto", "ceo", "founder", "co-founder", "vp", "director", "head of",
    "owner", "president", "managing director", "chief",
]


class LeadScorer:
    """
    Scores a lead/client prospect on a 0–100 scale.
    """

    def score(self, lead: dict) -> dict:
        industry = (lead.get("industry") or "").lower()
        pain_points = lead.get("pain_points") or []
        contact_role = (lead.get("contact_role") or "").lower()
        has_email = bool((lead.get("contact_email") or "").strip())
        company_size = lead.get("company_size", 0) or 0
        context = (lead.get("context_data") or {})

        industry_pts, industry_reason = self._score_industry(industry)
        pain_pts, pain_reason = self._score_pain_points(pain_points, context)
        contact_pts, contact_reason = self._score_contact(contact_role, has_email)
        size_pts, size_reason = self._score_size(company_size)

        total = min(100, industry_pts + pain_pts + contact_pts + size_pts)
        label = score_label(total)

        reasons = [r for r in [industry_reason, pain_reason, contact_reason, size_reason] if r]

        return {
            "lead_score": total,
            "score_label": label,
            "reasons": reasons,
            "breakdown": {
                "industry": industry_pts,
                "pain_signals": pain_pts,
                "contact_quality": contact_pts,
                "company_size": size_pts,
            },
        }

    def _score_industry(self, industry: str) -> tuple:
        for kw, pts in _TARGET_INDUSTRIES:
            if kw in industry:
                return pts, f"Target industry: {kw}"
        return 5, ""

    def _score_pain_points(self, pain_points: list, context: dict) -> tuple:
        pain_text = " ".join(str(p).lower() for p in pain_points)
        pain_text += " " + " ".join(str(v).lower() for v in context.values() if isinstance(v, str))
        total = 0
        matched = []
        for kw, pts in _PAIN_SIGNAL_KEYWORDS:
            if kw in pain_text:
                total += pts
                matched.append(kw)
        total = min(40, total)
        reason = f"Pain signals: {', '.join(matched[:3])}" if matched else ""
        return total, reason

    def _score_contact(self, role: str, has_email: bool) -> tuple:
        pts = 0
        reason_parts = []
        for kw in _CONTACT_ROLES_GOOD:
            if kw in role:
                pts += 20
                reason_parts.append(f"decision-maker role ({kw})")
                break
        if has_email:
            pts += 15
            reason_parts.append("email found")
        return min(35, pts), ", ".join(reason_parts) if reason_parts else ""

    def _score_size(self, size: int) -> tuple:
        if 10 <= size <= 200:
            return 10, f"Good company size ({size} employees)"
        if size > 200:
            return 5, "Larger company (harder to reach)"
        if size > 0:
            return 7, "Small company"
        return 5, ""
