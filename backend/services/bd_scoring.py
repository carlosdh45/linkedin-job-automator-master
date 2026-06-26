"""
Local, rule-based opportunity scoring. No external APIs. No AI calls.

Score components (max 100):
  - ICP match:              0–30
  - Pain point count:       0–20  (4 pts each, max 5)
  - Signal count:           0–20  (5 pts each, max 4)
  - Prospect seniority:     0–15
  - Urgency (days since signal): 0–10
  - Existing relationship:  0–5
"""
from typing import Optional


_SENIORITY_SCORES: dict[str, int] = {
    "c_suite": 15, "c-suite": 15, "ceo": 15, "cto": 15, "coo": 15, "cfo": 15,
    "vp": 13, "vice president": 13,
    "director": 10, "head of": 10,
    "manager": 6, "lead": 6,
    "engineer": 3, "analyst": 3, "ic": 3,
}


def _seniority_score(seniority: Optional[str]) -> int:
    if not seniority:
        return 0
    s = seniority.lower()
    for key, val in _SENIORITY_SCORES.items():
        if key in s:
            return val
    return 3  # any seniority recorded is worth something


def compute_opportunity_score(
    icp_match: bool,
    pain_point_count: int,
    signal_count: int,
    company_size: Optional[str],
    prospect_seniority: Optional[str],
    days_since_last_signal: Optional[int],
    existing_relationship: bool,
) -> tuple[int, str, dict]:
    breakdown: dict[str, int] = {}

    # ICP fit: max 30
    icp_pts = 30 if icp_match else 0
    breakdown["icp_match"] = icp_pts

    # Pain point count: 4 pts each, max 20
    pp_pts = min(pain_point_count * 4, 20)
    breakdown["pain_points"] = pp_pts

    # Signal count: 5 pts each, max 20
    sig_pts = min(signal_count * 5, 20)
    breakdown["signals"] = sig_pts

    # Prospect seniority: max 15
    sen_pts = _seniority_score(prospect_seniority)
    breakdown["seniority"] = sen_pts

    # Urgency: recent signals within 7 days = 10, within 30 = 5
    urgency_pts = 0
    if days_since_last_signal is not None:
        if days_since_last_signal <= 7:
            urgency_pts = 10
        elif days_since_last_signal <= 30:
            urgency_pts = 5
    breakdown["urgency"] = urgency_pts

    # Existing relationship: +5
    rel_pts = 5 if existing_relationship else 0
    breakdown["existing_relationship"] = rel_pts

    score = icp_pts + pp_pts + sig_pts + sen_pts + urgency_pts + rel_pts
    score = max(0, min(100, score))

    if score >= 75:
        label = "hot"
    elif score >= 55:
        label = "warm"
    elif score >= 30:
        label = "cold"
    else:
        label = "disqualified"

    return score, label, breakdown


def score_label_from_score(score: int) -> str:
    if score >= 75:
        return "hot"
    if score >= 55:
        return "warm"
    if score >= 30:
        return "cold"
    return "disqualified"
