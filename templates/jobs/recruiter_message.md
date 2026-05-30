# Template: Recruiter Message (Job Application)
# Style: recruiter_friendly
# Variables: contact_name, role_title, company_name, reason_for_fit, my_profile_summary, call_to_action

---
SYSTEM INSTRUCTION FOR CLAUDE:
Write a short, direct message from a candidate to a recruiter about a specific open role.

Rules:
- Open directly with context about the role — no "I hope this finds you well"
- Reference the specific {{role_title}} at {{company_name}}
- Mention 1-2 concrete skills or experiences from the candidate's profile
- Acknowledge LATAM/remote availability naturally
- End with a soft CTA — not desperate, not pushy
- Max 100 words
- No buzzwords, no excessive adjectives
- Sound like a real person wrote it at 9am on a Tuesday

---
EXAMPLE OUTPUT:

Hi {{contact_name}},

I saw the {{role_title}} role and it looks close to the kind of work I've been doing — software delivery, stakeholder coordination, technical execution across distributed teams.

I'm based in LATAM and work fully remote. Happy to share more context if the team is open to international candidates.

{{call_to_action}}

---
VARIABLES:
- my_profile_summary: Summary of candidate background
- company_name: Target company
- contact_name: Recruiter first name
- role_title: Exact job title from posting
- reason_for_fit: 1-2 sentence skill match explanation
- call_to_action: Soft closing (use RECRUITER_CTAS from humanizer.py)
- tone: recruiter_friendly
