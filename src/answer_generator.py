import anthropic
from src.cv_parser import CVProfile, profile_to_summary_text
from src.humanizer import style_instruction, FORBIDDEN_PHRASES


class AnswerGeneratorError(Exception):
    pass


class AnswerGenerator:
    def __init__(self, api_key: str, model: str, cv_profile: CVProfile, positioning: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.positioning = positioning
        self._system_prompt = self._build_system_prompt(cv_profile, positioning)

    def _build_system_prompt(self, profile: CVProfile, positioning: str) -> str:
        cv_summary = profile_to_summary_text(profile)
        forbidden = "\n".join(f'  - "{p}"' for p in FORBIDDEN_PHRASES[:10])
        return f"""You are a professional writer helping a candidate fill out job applications and write outreach.

Candidate positioning: {positioning}

Candidate CV:
{cv_summary}

Core rules:
- Answer ONLY what is asked. Output the answer only, no preamble.
- Be concise and direct. Sound like a real person, not an AI.
- For yes/no questions, answer "Yes" or "No".
- For numeric fields (years of experience), output only the number.
- For salary questions, use "Negotiable" unless specific data is in the CV.
- Never fabricate certifications, companies, degrees, or achievements not in the CV.
- For work authorization questions: answer "Yes" for Colombia and Latin America.
- Keep textarea answers under 150 words.
- Never use these phrases:
{forbidden}
"""

    def answer(
        self,
        question: str,
        field_type: str = "text",
        options: list = None,
        max_chars: int = None,
    ) -> str:
        user_content = f"Question: {question}\nField type: {field_type}"
        if options:
            user_content += f"\nAvailable options: {', '.join(str(o) for o in options)}"
            user_content += "\nChoose the best matching option and output ONLY that option text exactly."
        if max_chars:
            user_content += f"\nMax characters: {max_chars}"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                system=[
                    {
                        "type": "text",
                        "text": self._system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_content}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            raise AnswerGeneratorError(f"Claude API error: {e}") from e

    def answer_yes_no(self, question: str) -> str:
        return self.answer(question, field_type="radio", options=["Yes", "No"])

    def generate_outreach_email(
        self,
        company: str,
        job_title: str,
        contact_name: str = "",
        contact_role: str = "",
        positioning: str = "",
        style: str = "senior_pm_professional",
    ) -> tuple:
        positioning = positioning or self.positioning
        style_instr = style_instruction(style)
        greeting = f"Hi {contact_name.split()[0]}," if contact_name else "Hi,"

        prompt = f"""Write a professional outreach message using this style: {style}

Style instruction: {style_instr}

Context:
- Target company: {company}
- Role/position: {job_title or 'not specified'}
- Contact: {contact_name or 'unknown'} ({contact_role or 'unknown role'})
- Candidate positioning: {positioning}
- Start the message body with: {greeting}

Additional rules:
- Do not use any of these openers: "I hope this finds you well", "I came across your profile", "I was impressed"
- Be specific and human — mention the company or role name directly
- Under 150 words
- Include an unsubscribe line if this is a client email: "If this isn't relevant, just reply and I won't follow up."

Output format (exactly two lines at the start, nothing else before the body):
SUBJECT: <subject line>
BODY:
<message body>"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=[
                    {
                        "type": "text",
                        "text": self._system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            subject, body = self._parse_email_response(text)
            return subject, body
        except Exception as e:
            raise AnswerGeneratorError(f"Claude API error generating outreach: {e}") from e

    def _parse_email_response(self, text: str) -> tuple:
        if "SUBJECT:" in text and "BODY:" in text:
            subject = text.split("SUBJECT:")[1].split("\n")[0].strip()
            body = text.split("BODY:")[1].strip()
            return subject, body
        lines = text.split("\n")
        subject = lines[0].replace("Subject:", "").strip()
        body = "\n".join(lines[1:]).strip()
        return subject, body
