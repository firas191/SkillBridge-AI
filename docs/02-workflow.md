# SkillBridge AI — Workflow

The system is one shared pipeline: documents → structured skills → an explainable
match → downstream modules that all reuse the same trusted evidence base. LLM steps,
deterministic steps, external tools, and **human-review points** are marked below.

```mermaid
flowchart TD
    subgraph IN["Inputs"]
        CV["Candidate CV<br/>(paste / PDF / Word / image)"]
        JD["Job description<br/>(paste / PDF / Word / image)"]
    end

    OCR["Offline document reader<br/>(pdfplumber / python-docx / RapidOCR)"]
    HR1{{"Human review:<br/>verify extracted text"}}

    CV --> OCR --> HR1
    JD --> OCR

    subgraph EXTRACT["Extraction — LLM chains (structured JSON + repair)"]
        CE["Candidate extraction<br/>skills + evidence + proficiency"]
        JE["Job extraction<br/>weighted requirements"]
        GG["Grounding guard<br/>(drops hallucinated requirements)"]
        JE --> GG
    end

    HR1 --> CE
    JD --> JE

    NORM["Skill normalizer<br/>→ canonical taxonomy (ESCO-mergeable)"]
    CE --> NORM
    GG --> NORM

    ENGINE["Explainable Match Engine<br/>(deterministic, no LLM)"]
    NORM --> ENGINE

    RESULT["MatchResult<br/>score · verdict · per-skill rationale · evidence · gaps"]
    ENGINE --> RESULT

    subgraph DOWN["Downstream modules (reuse the evidence base)"]
        COACH["Adaptive Learning Coach<br/>LLM + resource catalog"]
        SIM["Interview Simulator<br/>LLM (questions + rubric grading)"]
        AGENT["HR Agent<br/>tools: salary · demand · outlook · guidelines → LLM"]
    end

    RESULT --> COACH
    RESULT --> SIM
    RESULT --> AGENT

    HR2{{"Human review:<br/>recruiter weighs the brief,<br/>makes the final decision"}}
    AGENT --> HR2

    TWIN["AI Career Twin<br/>(persistence + aggregation + LLM briefing)"]
    RESULT --> TWIN
    SIM --> TWIN
    COACH --> TWIN

    OUT["Outputs<br/>gap map · learning roadmap · interview debrief ·<br/>recruiter brief · living career profile"]
    COACH --> OUT
    SIM --> OUT
    HR2 --> OUT
    TWIN --> OUT
```

## Where the LLM is used vs. where it isn't

- **LLM (reasoning):** candidate/job extraction, learning-plan generation, interview
  question generation + grading, HR brief synthesis, Career-Twin briefing.
- **Deterministic (reproducible):** skill normalization, the match engine and its score,
  the grounding guard, the salary/demand/outlook tools, the interview overall score
  (computed from per-answer grades), Career-Twin aggregation.

This split is deliberate: the LLM handles language understanding; the **scoring and the
evidence are deterministic**, so results are explainable and reproducible.

## Human-review points (decision support, not automation)

1. **Extracted-text verification** — uploaded documents land in an editable box; the
   user confirms before matching.
2. **Final hiring decision** — the HR Agent's brief is explicitly advisory, with a
   human-in-the-loop disclaimer and fair-hiring guidelines; a recruiter decides.
