# SkillBridge AI — Project Brief

**An explainable, skill-based copilot connecting education to employment.**

## The problem

Education and recruitment are disconnected. Learners finish courses without knowing
whether they're ready for real jobs. Educators lack a clear view of market needs.
Recruiters spend hours screening CVs by keyword and overlook strong, non-traditional
candidates. Interview preparation is rarely realistic or role-specific.

## Users and the value delivered

| User | Value |
|------|-------|
| **Learners** | A clear, evidence-backed picture of missing skills and a concrete plan to close them. |
| **Recruiters** | Explainable, skills-based screening with the evidence behind every match. |
| **Hiring managers** | A tool-grounded, advisory recruiter brief and role-specific interview questions. |
| **Educators** | Visibility into skill gaps and learning paths (via the same shared evidence base). |

## The solution

SkillBridge turns a CV and a job description into a **structured skill graph**, scores
the fit **transparently** (every match cites the line that proves it), and turns the
gaps into action across five modules plus an evolving profile:

1. **Learner Skill Scanner** — evidence-backed skill extraction, a gap map, a readiness score.
2. **Recruitment Match Engine** — explainable candidate↔role scoring with rationale.
3. **Adaptive Learning Coach** — gaps → a sequenced roadmap with practice projects, resources, and weekly missions.
4. **Interview Simulator** — a role-specific mock interview with a rubric-scored debrief.
5. **HR Agent (with tools)** — gathers live market evidence (salary, demand, outlook, fair-hiring guidelines) into an advisory recruiter brief.
6. **AI Career Twin** *(innovative extension)* — a persistent profile that accumulates matches, interviews, and learning over time into a living briefing.

## How it's built (at a glance)

- **Stack:** FastAPI (Python) + React/TypeScript, SQLite persistence.
- **LLM:** provider-agnostic — NVIDIA NIM, Google Gemini, or local Ollama, switchable via one env var.
- **Techniques:** iterative prompt engineering, structured (JSON) output with a repair pass,
  a canonical skill taxonomy (curated seed, ESCO-mergeable), a deterministic explainable
  match engine, an anti-hallucination grounding guard, and tool-using agents.
- **Offline document intake:** PDF / Word / image (OCR) read locally with no API key.
- **Quality:** ~45 automated tests; an extraction-recall evaluation harness.

## Measured impact targets (from the brief)

| Metric | Target |
|--------|--------|
| Manual CV screening time | −40% |
| Learner role readiness | +30% |
| Qualified shortlist quality | +25% |
| Explainability of recommendations | 100% (required) |
| Interview preparation quality | +35% |

## Deliverables in this folder

- `01-project-brief.md` — this document.
- `02-workflow.md` — the end-to-end workflow diagram with human-review points.
- `03-prompt-library.md` — the prompt library and the engineering technique behind each.
- `04-structured-outputs.md` — sample structured (JSON) outputs per module.

The full project overview, features, setup, and API live in the root
[`README.md`](../README.md).
