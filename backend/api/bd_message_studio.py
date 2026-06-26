"""
Message Studio — local, rule-based draft generation only.
No external API calls. No automatic sending. No LinkedIn API. No Gmail API.
All drafts are marked for manual review.
"""
from fastapi import APIRouter

from backend.models.bd import BDMessageDraftRequest, BDMessageDraftResponse

router = APIRouter(prefix="/bd/message-studio", tags=["bd-message-studio"])

_SAFETY_NOTICE = "Prepared for manual review. DobryBot does not send automatically."

_EMAIL_TEMPLATE = """\
Subject: {subject}

Hi {first_name},

{opening}

{value_statement}

{cta}

[Your name]

---
{safety_notice}"""

_LINKEDIN_TEMPLATE = """\
Hi {first_name}, {opening_short} Would love to share what we've seen work for similar teams. Open to a quick chat?

---
{safety_notice}"""

_INTRO_TEMPLATE = """\
Hi [Mutual connection],

Could you introduce me to {contact_name} at {company_name}? {intro_reason}

I'm not looking to pitch — just a conversation to see if it makes sense to explore further. Happy to make it easy with a quick intro draft if helpful.

Thanks!

---
{safety_notice}"""


def _tone_opening(tone: str, company: str, pain_point: str) -> tuple[str, str]:
    """Returns (opening paragraph, short opening for LinkedIn)."""
    pain = pain_point.lower() if pain_point else "your current priorities"
    if tone == "executive":
        opening = f"I've been studying {company}'s trajectory and see a clear alignment around {pain}."
        short = f"I've been following {company}'s work and see a clear connection around {pain}."
    elif tone == "technical":
        opening = f"I noticed {company} is working through some interesting challenges around {pain} — I've worked closely on similar problems."
        short = f"I noticed {company}'s approach to {pain} — we've solved similar challenges."
    elif tone == "direct":
        opening = f"Quick note: I think there's a concrete way to reduce {pain} at {company}."
        short = f"Saw {company}'s work on {pain} — think there's a concrete opportunity here."
    else:  # warm
        opening = f"I've been following {company}'s work and noticed you're navigating some challenges around {pain}."
        short = f"I saw {company} is scaling fast — impressive growth."

    return opening, short


def _value_statement(company: str, angle: str, pain_point: str) -> str:
    topic = angle if angle else (pain_point if pain_point else "your priorities")
    return (
        f"We've helped teams like {company}'s address {topic.lower()} — "
        "typically delivering measurable improvements in 6–8 weeks without disrupting existing workflows."
    )


def _cta(message_type: str) -> str:
    return "Would a 20-minute call to share what's worked for comparable organizations be worth your time?"


@router.post("/draft", response_model=BDMessageDraftResponse)
def generate_draft(req: BDMessageDraftRequest) -> BDMessageDraftResponse:
    """
    Generate a local outreach draft using rule-based templates.
    No external APIs. No AI calls. Draft is marked for manual review.
    """
    first_name = req.contact_name.split()[0] if req.contact_name else "there"
    opening, short_opening = _tone_opening(req.tone, req.company_name, req.pain_point)
    value_stmt = _value_statement(req.company_name, req.angle, req.pain_point)
    cta = _cta(req.message_type)

    subject: str | None = None

    if req.message_type == "email":
        topic = req.pain_point or req.angle or "your current priorities"
        subject = f"Solving {topic.lower()} at {req.company_name}"
        draft = _EMAIL_TEMPLATE.format(
            subject=subject,
            first_name=first_name,
            opening=opening,
            value_statement=value_stmt,
            cta=cta,
            safety_notice=_SAFETY_NOTICE,
        )
    elif req.message_type == "linkedin":
        draft = _LINKEDIN_TEMPLATE.format(
            first_name=first_name,
            opening_short=short_opening,
            safety_notice=_SAFETY_NOTICE,
        )
    else:  # intro_request
        pain = req.pain_point or req.angle or "strategic priorities"
        intro_reason = (
            f"I've been following their work and think there's a strong alignment around {pain.lower()}."
        )
        draft = _INTRO_TEMPLATE.format(
            contact_name=req.contact_name or "the team",
            company_name=req.company_name,
            intro_reason=intro_reason,
            safety_notice=_SAFETY_NOTICE,
        )

    return BDMessageDraftResponse(
        draft=draft,
        subject=subject,
        safety_notice=_SAFETY_NOTICE,
        message_type=req.message_type,
        tone=req.tone,
    )
