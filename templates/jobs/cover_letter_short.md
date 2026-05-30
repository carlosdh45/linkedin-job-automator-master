# Template: Short Cover Letter (Job Application)
# Style: senior_pm_professional
# Variables: contact_name, role_title, company_name, reason_for_fit, specific_context, my_profile_summary, call_to_action

---
SYSTEM INSTRUCTION FOR CLAUDE:
Write a short, professional cover letter for a job application.

Rules:
- 3 short paragraphs max
- Paragraph 1: Why this role at this company specifically (reference {{specific_context}})
- Paragraph 2: Most relevant experience — 2 concrete examples, no fluff
- Paragraph 3: One line CTA + availability
- Max 180 words total
- No "I am writing to express my interest" openers
- No lists of adjectives ("dynamic", "passionate", "motivated")
- Every sentence must earn its place

---
EXAMPLE OUTPUT:

{{contact_name}},

The {{role_title}} caught my attention because {{specific_context}}. That's exactly the kind of work I've been doing for the past several years.

At [Company], I [concrete achievement 1]. More recently, [concrete achievement 2]. Both required the mix of technical depth and stakeholder management that this role seems to need.

Open to a conversation if there's fit. I'm based in LATAM, fully remote.

---
VARIABLES:
- my_profile_summary: Full CV summary
- company_name: Target company
- contact_name: Hiring manager or recruiter name (or "Hi" if unknown)
- role_title: Exact job title
- specific_context: Something specific about the company or role that makes this relevant
- reason_for_fit: Key skill match explanation
- call_to_action: Soft closing
- tone: senior_pm_professional
