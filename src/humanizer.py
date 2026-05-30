"""
Message humanization: forbidden-phrase detection, style system prompt fragments,
and context-completeness validation.
"""

# ── Forbidden phrases ─────────────────────────────────────────────────────────

FORBIDDEN_PHRASES = [
    "I hope this message finds you well",
    "I hope this email finds you well",
    "I came across your profile",
    "I was impressed by your company",
    "In today's fast-paced digital world",
    "I am reaching out to",
    "I wanted to reach out",
    "I would love to connect",
    "I am excited to",
    "Please don't hesitate to",
    "Looking forward to hearing from you",
    "I believe I would be a great fit",
    "I am passionate about",
    "synergies",
    "leverage",
    "thought leader",
    "game-changer",
    "revolutionary",
    "cutting-edge solutions",
    "best-in-class",
    "world-class",
    "value proposition",
    "take your business to the next level",
    "I can help you achieve",
    "transformative results",
    "touch base",
    "circle back",
    "at your earliest convenience",
]


def check_forbidden_phrases(text: str) -> list:
    """Return a list of forbidden phrases found in the text."""
    found = []
    text_lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in text_lower:
            found.append(phrase)
    return found


# ── Message styles ─────────────────────────────────────────────────────────────

STYLES = {
    "founder_direct": {
        "description": "Direct founder-to-founder or founder-to-decision-maker tone. Short, honest, no fluff.",
        "instruction": (
            "Write as a hands-on founder. Be direct and brief. "
            "Skip pleasantries. Lead with the specific reason you're reaching out. "
            "One concrete observation about their business. One clear ask. Max 100 words."
        ),
    },
    "senior_pm_professional": {
        "description": "Senior PM or delivery professional reaching out about a role.",
        "instruction": (
            "Write as a senior PM/delivery professional. Professional but not stiff. "
            "Reference the specific role and one concrete skill match. "
            "No buzzwords. No generic opener. Max 120 words."
        ),
    },
    "warm_networking": {
        "description": "Warm, conversational, genuine curiosity about the person's work.",
        "instruction": (
            "Write as someone genuinely curious about the person's work. "
            "Mention something specific about their company or role. "
            "No pitch. Just an honest opener and a soft ask to connect. Max 80 words."
        ),
    },
    "client_value_first": {
        "description": "Lead with a specific observation about the client's business, then offer value.",
        "instruction": (
            "Open with one specific, real observation about their business situation. "
            "Offer one concrete way you might be able to help. "
            "No generic pitch. No list of services. Max 120 words. "
            "End with a low-pressure CTA: a short call or 'let me know if this is relevant'."
        ),
    },
    "recruiter_friendly": {
        "description": "Candidate messaging a recruiter about a specific open role.",
        "instruction": (
            "Write as a strong candidate reaching out to a recruiter. "
            "Reference the specific role title. Mention 2 concrete skills/experiences. "
            "Acknowledge you're based in LATAM/remote. Soft ask for a conversation. "
            "No desperation. No over-selling. Max 100 words."
        ),
    },
}


def style_instruction(style_key: str) -> str:
    style = STYLES.get(style_key, STYLES["senior_pm_professional"])
    return style["instruction"]


# ── Context completeness validation ───────────────────────────────────────────

REQUIRED_CONTEXT_FIELDS = {
    "job": ["company", "job_title"],
    "client": ["company", "industry"],
}

ENRICHING_CONTEXT_FIELDS = {
    "job": ["contact_name", "contact_role", "specific_signal"],
    "client": ["contact_name", "contact_role", "pain_point", "specific_signal"],
}


def has_sufficient_context(context: dict, outreach_type: str = "client") -> tuple:
    """
    Returns (ok: bool, missing: list[str]).
    At least one enriching field must be present in addition to required fields.
    """
    required = REQUIRED_CONTEXT_FIELDS.get(outreach_type, [])
    enriching = ENRICHING_CONTEXT_FIELDS.get(outreach_type, [])

    missing_required = [f for f in required if not context.get(f, "").strip()]
    if missing_required:
        return False, missing_required

    has_enriching = any(context.get(f, "").strip() for f in enriching)
    if not has_enriching:
        return False, enriching  # caller knows none of these were present

    return True, []


# ── CTA library ───────────────────────────────────────────────────────────────

SOFT_CTAS = [
    "Would a 15-minute call make sense?",
    "Happy to share more context if helpful.",
    "Let me know if this is relevant — no pressure.",
    "Open to a quick call if the timing works.",
    "If it's not the right moment, no worries at all.",
]

RECRUITER_CTAS = [
    "Happy to share more context if the team is open to LATAM candidates.",
    "Let me know if it makes sense to talk.",
    "Open to a quick intro call if helpful.",
]


def get_cta(outreach_type: str = "client", style: str = "client_value_first") -> str:
    if outreach_type == "job" or style == "recruiter_friendly":
        return RECRUITER_CTAS[0]
    return SOFT_CTAS[0]
