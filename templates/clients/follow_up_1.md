# Template: Follow-up #1 (Client Outreach — 5-7 days after first touch)
# Style: founder_direct
# Variables: contact_name, company_name, original_subject, specific_context, call_to_action

---
SYSTEM INSTRUCTION FOR CLAUDE:
Write a follow-up email, sent 5-7 days after the first touch with no response.

Rules:
- Very short — max 60 words
- Reference the original email (short, not a full copy)
- Add ONE new piece of value or context — don't just say "checking in"
- No guilt-tripping ("I know you're busy...")
- No "just following up" opener
- End with an opt-out option

---
EXAMPLE OUTPUT:

Hi {{contact_name}},

Sending a quick follow-up on my note last week about {{specific_context}}.

One thing I didn't mention: {{new_value_or_context}}.

If the timing's off, happy to circle back another time.

{{call_to_action}}

---
VARIABLES:
- contact_name: First name
- company_name: Target company
- original_subject: Subject line of first email
- specific_context: The core observation from first email (brief)
- new_value_or_context: One additional useful fact or idea (not in first email)
- call_to_action: Low-pressure ask
- tone: founder_direct
