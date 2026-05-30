"""
Quality Guard: scores outreach drafts before they can be approved.

Uses a single Claude API call with prompt caching to evaluate:
- personalization_score (0-100): how specific/real is the personalization?
- spam_risk_score (0-100): how spammy does this look?
- ai_sounding_score (0-100): how obviously AI-generated does this sound?

Thresholds (must ALL pass to be approvable):
  personalization_score >= 75
  spam_risk_score       <= 35
  ai_sounding_score     <= 40
"""

import json
import logging

import anthropic

from src.humanizer import check_forbidden_phrases

logger = logging.getLogger(__name__)

PASS_THRESHOLDS = {
    "personalization_score": (">=", 75),
    "spam_risk_score": ("<=", 35),
    "ai_sounding_score": ("<=", 40),
}

_SYSTEM_PROMPT = """You are a quality auditor for professional outreach messages.
Your job: score a message on 3 dimensions and give actionable feedback.

Scoring dimensions:
1. personalization_score (0–100)
   100 = message mentions specific, verifiable details about the company/person/role
   50  = mentions company name but nothing else specific
   0   = completely generic, could be sent to anyone

2. spam_risk_score (0–100)
   100 = clearly spam (mass template, unsolicited bulk, fake urgency)
   50  = borderline (some generic language, vague offer)
   0   = legitimate, targeted, professional

3. ai_sounding_score (0–100)
   100 = obviously AI-written (overly formal, no natural pauses, buzzwords)
   50  = slightly robotic but passable
   0   = sounds like a real human wrote it

Rules:
- Be strict. A message that mentions the company name but nothing specific scores ≤ 50 on personalization.
- Penalize: "I hope this finds you well", "I came across your profile", "synergies", "leverage", "passionate about"
- Reward: specific role mention, real pain point, industry signal, concrete skill reference
- Reward: short sentences, contractions, occasional informality
- Do NOT fabricate reasons. Only score what's in the message.

Respond in valid JSON only. No prose before or after the JSON.
{
  "personalization_score": 0-100,
  "spam_risk_score": 0-100,
  "ai_sounding_score": 0-100,
  "quality_reasons": ["reason 1", "reason 2"],
  "send_recommendation": "send" | "revise" | "skip",
  "improvement_tip": "one specific suggestion to improve the message"
}"""


class QualityGuard:
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        # Haiku is fast and cheap for quality checks
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def score_message(self, message_body: str, context: dict) -> dict:
        """
        Score a message. Returns the full scoring dict.
        context keys: company, job_title/role, contact_name, contact_role, outreach_type
        """
        # Pre-check forbidden phrases (free, no API call)
        forbidden = check_forbidden_phrases(message_body)

        user_prompt = self._build_user_prompt(message_body, context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = response.content[0].text.strip()
            scores = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("QualityGuard: Claude returned non-JSON — using fallback scores")
            scores = self._fallback_scores()
        except Exception as e:
            logger.warning(f"QualityGuard API error: {e} — using fallback scores")
            scores = self._fallback_scores()

        # Merge forbidden-phrase info into reasons
        if forbidden:
            scores.setdefault("quality_reasons", [])
            scores["quality_reasons"].append(
                f"Forbidden phrases detected: {', '.join(forbidden[:3])}"
            )
            scores["ai_sounding_score"] = min(100, scores.get("ai_sounding_score", 50) + 20)

        scores["passes"] = self.passes_threshold(scores)
        scores["word_count"] = len(message_body.split())
        return scores

    def passes_threshold(self, scores: dict) -> bool:
        for field, (op, threshold) in PASS_THRESHOLDS.items():
            val = scores.get(field, 0)
            if op == ">=" and val < threshold:
                return False
            if op == "<=" and val > threshold:
                return False
        return True

    def _build_user_prompt(self, body: str, context: dict) -> str:
        ctx_lines = []
        if context.get("company"):
            ctx_lines.append(f"Company: {context['company']}")
        if context.get("job_title") or context.get("role"):
            ctx_lines.append(f"Role: {context.get('job_title') or context.get('role')}")
        if context.get("contact_name"):
            ctx_lines.append(f"Contact: {context['contact_name']}")
        if context.get("contact_role"):
            ctx_lines.append(f"Contact role: {context['contact_role']}")
        if context.get("pain_point"):
            ctx_lines.append(f"Known pain point: {context['pain_point']}")
        ctx_block = "\n".join(ctx_lines) if ctx_lines else "(no additional context)"

        return f"""CONTEXT:
{ctx_block}

MESSAGE TO SCORE:
---
{body}
---

Score this message strictly. Respond in JSON only."""

    def _fallback_scores(self) -> dict:
        return {
            "personalization_score": 40,
            "spam_risk_score": 60,
            "ai_sounding_score": 60,
            "quality_reasons": ["Could not reach quality API — conservative fallback scores applied"],
            "send_recommendation": "revise",
            "improvement_tip": "Review manually before sending.",
        }


def format_quality_report(scores: dict) -> str:
    """Format quality scores for terminal display."""
    p = scores.get("personalization_score", 0)
    s = scores.get("spam_risk_score", 0)
    a = scores.get("ai_sounding_score", 0)
    passes = scores.get("passes", False)

    p_status = "PASS" if p >= 75 else "FAIL"
    s_status = "PASS" if s <= 35 else "FAIL"
    a_status = "PASS" if a <= 40 else "FAIL"

    lines = [
        f"  Personalization : {p:3d}/100  [{p_status}]  (need ≥75)",
        f"  Spam risk       : {s:3d}/100  [{s_status}]  (need ≤35)",
        f"  AI-sounding     : {a:3d}/100  [{a_status}]  (need ≤40)",
        f"  Words           : {scores.get('word_count', '?')}",
        f"  Recommendation  : {scores.get('send_recommendation', '?').upper()}",
        f"  Overall         : {'✓ APPROVABLE' if passes else '✗ NEEDS REVISION'}",
    ]
    reasons = scores.get("quality_reasons", [])
    if reasons:
        lines.append("  Issues found:")
        for r in reasons:
            lines.append(f"    - {r}")
    tip = scores.get("improvement_tip", "")
    if tip:
        lines.append(f"  Tip: {tip}")
    return "\n".join(lines)
