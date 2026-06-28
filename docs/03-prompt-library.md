# SkillBridge AI — Prompt Library

Seven production prompts power the LLM reasoning. Each pairs a **system** prompt (role
+ rules) with a **template** (the data + an explicit JSON shape). All use low/zero
temperature and a JSON-repair fallback for robust structured output. Full text lives in
the `*/prompts.py` files referenced below.

---

### 1. Skill extraction (candidate) — `services/extraction/prompts.py`

**Purpose:** parse a CV into evidence-backed skills.
**Techniques:** structured output; *implicit-skill inference* ("mentored juniors / led
ceremonies" → Leadership, Teamwork, Agile); evidence prioritisation (cite a concrete
achievement, not the skills-list line); anti-over-inference guard.

> "Infer skills that are clearly IMPLIED by experience… `evidence` must quote the
> STRONGEST supporting line, preferring concrete achievements with metrics over the
> generic 'Skills' list… Do NOT claim a distinct skill from a merely adjacent field."

### 2. Job extraction — `services/extraction/prompts.py`

**Purpose:** extract weighted, importance-classified requirements.
**Techniques:** importance calibration (intern/junior roles → learnable platforms are
*preferred*, not *required*); "at least one of A/B/C" → one requirement with
`alternatives`; no academic fields as skills; atomic skill names. Paired with a
deterministic **grounding guard** that drops any requirement absent from the posting.

### 3. Learning recommendation — `services/learning/prompts.py`

**Purpose:** turn gaps into a sequenced roadmap.
**Techniques:** prioritise by prerequisites; **leverage existing strengths**; every
module yields a portfolio practice project; weekly missions end in a deliverable;
resources favour real, well-known sources.

### 4. Interview simulation — questions — `services/interview/prompts.py`

**Purpose:** generate a tailored mock interview.
**Techniques:** a balanced set (technical probing real strengths, behavioural, a *gap*
question assessing ramp-up, motivation); each question carries `what_good_looks_like`
for fair grading later.

### 5. Interview simulation — grading — `services/interview/prompts.py`

**Purpose:** score the answered transcript.
**Techniques:** a calibrated, **anti-inflation** 0–5 rubric ("if every answer is a 5,
you are grading too softly"); per-answer reasons for points lost. The overall score is
**computed deterministically** from the per-answer grades, not asked of the model.

### 6. Recruiter summary — `services/hr/prompts.py`

**Purpose:** synthesise an advisory recruiter brief from tool evidence.
**Techniques:** reason explicitly from gathered tool data (salary, demand, outlook);
choose an advisory `decision`; **responsible-AI framing** — skills/evidence only, never
background; a human-in-the-loop disclaimer.

### 7. Career-Twin briefing — `services/twin/prompts.py`

**Purpose:** read accumulated activity into a living briefing.
**Techniques:** aggregate-aware (roles explored, best fit, recurring gaps, interview
average); motivating, second-person; concrete next missions.

---

## Cross-cutting prompt-engineering decisions

- **Explicit JSON shapes in the template** (rather than relying solely on function
  calling) so the same prompts work across NVIDIA NIM, Gemini, and local Ollama.
- **Robust parsing:** strip code fences → extract the JSON object → validate against a
  Pydantic schema → one *repair* retry if parsing fails.
- **Low/zero temperature** for faithful, reproducible structure.
- **Determinism where it matters:** scores and evidence are computed in code, not by the
  model, so every recommendation is explainable and reproducible.
