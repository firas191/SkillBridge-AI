"""Prompt templates for structured extraction.

The JSON shape is written out explicitly (rather than relying solely on native
function-calling) so the prompts work identically on NVIDIA NIM Llama 3.1 and
on a local Ollama model. Temperature is kept low at the model layer.
"""
from __future__ import annotations

CANDIDATE_SYSTEM = """You are an expert technical recruiter and resume parser.
Extract a complete, structured profile from the candidate CV provided by the user.

COVERAGE — do not under-extract:
- Capture BOTH technical/hard skills and soft skills.
- Infer skills that are clearly IMPLIED by experience, projects and achievements
  — not only those printed in a "Skills" section. Sound inferences include:
    * "mentored juniors" / "led the team" / "led agile ceremonies"
        -> Leadership, Mentoring, Teamwork, Agile
    * "designed database schemas" / "optimized slow queries"
        -> Database Design, SQL (and the specific database)
    * "deployed to AWS ECS" / "containerized services"
        -> AWS, Docker, CI/CD
    * "collaborated with product and design"
        -> Teamwork, Communication
- Do NOT invent skills that have no basis in the text.
- Do NOT claim a distinct skill from a merely adjacent field (e.g. don't list
  "Data Warehousing" just because the CV says "Data Science").

EVIDENCE — make it specific:
- `evidence` must quote or closely paraphrase the STRONGEST supporting line,
  preferring concrete achievements from EXPERIENCE or PROJECTS (with metrics
  where present) OVER the generic comma-separated "Skills" list.
- Use the Skills-list line as evidence ONLY when no experiential evidence exists
  for that skill.

SCORING:
- `proficiency` (beginner|intermediate|advanced|expert) and `years_experience`
  only when reasonably inferable; otherwise null.
- `confidence` is your 0.0-1.0 certainty the candidate genuinely has the skill.

Respond with ONLY a single valid JSON object. No prose, no code fences."""

CANDIDATE_TEMPLATE = """Return JSON with exactly this shape:
{{
  "name": "string",
  "headline": "string or null",
  "summary": "string or null",
  "total_years_experience": number or null,
  "skills": [
    {{
      "name": "string",
      "evidence": "string or null",
      "proficiency": "beginner|intermediate|advanced|expert or null",
      "years_experience": number or null,
      "confidence": 0.0
    }}
  ],
  "education": ["string"],
  "experience": [
    {{"title": "string or null", "company": "string or null",
      "duration": "string or null", "highlights": ["string"]}}
  ],
  "certifications": ["string"]
}}

Evidence quality guide:
  GOOD -> "Mentored two junior engineers and led agile ceremonies"
  WEAK -> "communication, teamwork"   (don't use the skills list when a real
                                        achievement line exists for the skill)

CV:
\"\"\"
{cv}
\"\"\"
"""

JOB_SYSTEM = """You are an expert hiring manager and job-description analyst.
Extract the structured skill requirements from the job posting provided.

Rules:
- Extract ONLY skills explicitly stated or unambiguously required by THIS
  posting. Do NOT invent skills that are merely common for the role.
- Use SHORT, atomic skill names (1-3 words); no parenthetical descriptions
  (write "English", not "English (professional working proficiency)").
- Do NOT extract broad academic fields or degrees as skills (e.g. "Computer
  Science", "Data", "Engineering", "Business", "a related field"). Those are
  education background, not skills.
- Output ONLY skills the posting actually states. Never invent a skill from an
  unrelated domain (e.g. do not output "iOS", "Android" or "Mobile" for a role
  that never mentions them).
- Avoid vague umbrella phrases ("Building Solutions", "Problem Solving" as a
  hard skill); name the concrete skill or tool the text actually states.

IMPORTANCE — be conservative with "required". Mislabeling learnable tools as
required unfairly penalises strong candidates:
- "required": genuinely must-have to start the job — "must have", "X+ years
  required", "strong/expert in", or a skill named as essential.
- "preferred": desired but not a hard gate ("ideally", "experience with",
  "comfortable with"). For INTERNSHIP / junior roles, specific platforms the
  hire would be onboarded onto (e.g. Salesforce, Zendesk, BigQuery, Slack,
  Jira, HubSpot, internal tools) are "preferred" — interns LEARN these — unless
  the posting explicitly requires prior experience with that exact tool.
- "nice_to_have": bonus ("a plus", "exposure to", "familiarity with").

ALTERNATIVES ("at least one of"):
- When the posting accepts ANY ONE of several interchangeable options ("at least
  one of A, B, C", "A, B, or C", "X / Y / Z or similar"), output ONE requirement:
  put the most standard option in `name` and the rest in `alternatives`. Do NOT
  create a separate required skill for each option.
- But when several DISTINCT tools are ALL used ("integrate with A, B and C"),
  list them separately.

- Include `min_years` only when the posting states or clearly implies it.
- Capture hard and important soft skills; merge duplicates (keep highest importance).
- Respond with ONLY a single valid JSON object. No prose, no code fences."""

JOB_TEMPLATE = """Return JSON with exactly this shape:
{{
  "title": "string",
  "company": "string or null",
  "seniority": "string or null",
  "summary": "string or null",
  "required_skills": [
    {{"name": "string",
      "importance": "required|preferred|nice_to_have",
      "min_years": number or null,
      "alternatives": ["string"]}}
  ],
  "responsibilities": ["string"]
}}

JOB POSTING:
\"\"\"
{job}
\"\"\"
"""

REPAIR_TEMPLATE = """The following text was supposed to be a single valid JSON
object but could not be parsed. Fix it and return ONLY the corrected JSON
object, with no commentary or code fences.

INVALID OUTPUT:
\"\"\"
{bad}
\"\"\"
"""
