# Template: First Touch Client Outreach Email
# Style: client_value_first
# Variables: contact_name, company_name, pain_point, specific_context, reason_for_fit, call_to_action

---
SYSTEM INSTRUCTION FOR CLAUDE:
Write a first-touch cold outreach email from a nearshore software/product consultant to a potential client.

Rules:
- Open with ONE specific, real observation about their business — not a compliment, an observation
- Never say "I came across your company" or "I was impressed by"
- Offer a concrete way you might be able to help, tied to the observed pain
- Keep it under 120 words
- End with a low-pressure CTA: a 15-minute call or "let me know if this is relevant"
- Add opt-out line at the bottom: "If this isn't relevant, just reply with 'not interested' and I won't follow up."
- Sound like a founder, not a sales rep

---
EXAMPLE OUTPUT:

Hi {{contact_name}},

I noticed {{specific_context}}. I work with a small nearshore team helping companies clean up workflows, CRM processes, and internal tools — usually in 4-6 weeks.

Not sure if {{pain_point}} is something you're actively working on, but if {{company_name}} is thinking about it, I'd be happy to share a few ideas.

{{call_to_action}}

If this isn't relevant right now, no worries — just reply and I won't follow up.

---
VARIABLES:
- my_profile_summary: Brief consultant background
- company_name: Target company
- contact_name: Decision-maker first name
- pain_point: Observed or inferred pain (e.g., "automating lead qualification")
- specific_context: Real, verifiable observation about the company
- reason_for_fit: Why your services match their situation
- call_to_action: Soft CTA (use SOFT_CTAS from humanizer.py)
- tone: client_value_first
