# SkillBridge AI

An explainable, skill-based copilot that connects **education to employment** —
parsing CVs and job descriptions into a structured skill graph, then producing
transparent, evidence-backed match decisions instead of brittle keyword screens.

This repository is a **production-oriented build**, not a demo notebook. The
LLM layer is provider-agnostic, the skill vocabulary is a real taxonomy
(curated seed, mergeable with the full EU **ESCO** classification), and the
core engine ships with a deterministic, offline test suite.

> **Status — Iteration 1: the foundation.** We deliberately started with the
> hardest, most load-bearing module: **structured skill extraction + the
> explainable match engine**. Every other module in the brief (learning coach,
> interview simulator, HR agent, AI Career Twin) consumes the skill graph this
> module produces, so building it first de-risks the entire project. See the
> [Roadmap](#roadmap).

---

## Why these engineering choices

**Provider-agnostic LLM (NVIDIA NIM ↔ local Ollama, one env var).**
The brief specifies NVIDIA NIM + Llama 3.1. NIM's free tier is real but
*limited* (~1k–5k credits, ~40 req/min), which is fine for development but
would throttle a real product. So the entire app talks to the model through a
single factory (`app/core/llm.py`). Set `LLM_PROVIDER=nvidia` to use NIM's free
credits today; switch to `LLM_PROVIDER=openai_compatible` pointed at a local
**Ollama** running Llama 3.1 for free, unlimited, fully-private inference — with
**zero code changes**.

**Explainability is structural, not cosmetic.** Both sides are normalized onto
a canonical skill taxonomy, so a candidate's "ReactJS" and a job's "React.js"
compare on the same ID. The match score is a transparent weighted average; each
requirement carries a status (matched / partial / missing), a rationale, and the
candidate's supporting evidence snippet. Adjacent skills (taxonomy "related"
links) earn *partial* credit — this is what surfaces strong non-traditional
candidates that keyword filters drop.

**Deterministic core.** The scoring engine and skill normalizer make **no LLM
calls**, so results are reproducible and the test suite runs offline with no API
key.

---

## Architecture

```
CV / Job text
     │
     ▼
[ Extraction chains ]  LangChain + Llama 3.1 → strict JSON (Raw* schemas)
     │                 robust parser w/ JSON-repair retry (portable across providers)
     ▼
[ Skill normalizer ]  free-text skill → canonical taxonomy ID
     │                 exact → fuzzy (RapidFuzz) → semantic (optional embeddings)
     ▼
[ Match engine ]      canonical candidate skills × weighted job requirements
     │                 → matched/partial/missing + rationale + evidence
     ▼
[ MatchResult ]       overall score, verdict, coverage, gaps, learning recs
     │
     ├── FastAPI  (REST + OpenAPI docs at /docs, SQLite persistence)
     └── React UI (paste CV + job → explainable result)
```

### Repository layout

```
SkillBridge AI/
├── backend/
│   ├── app/
│   │   ├── core/         config, logging, provider-agnostic LLM factory
│   │   ├── db/           SQLAlchemy models + session
│   │   ├── schemas/      Pydantic: extraction, match, API I/O
│   │   ├── services/
│   │   │   ├── taxonomy/   canonical skill store + normalizer
│   │   │   ├── extraction/ document parsing + LLM extraction chains
│   │   │   └── matching/   explainable match engine (deterministic)
│   │   ├── api/routes/   health, candidates, jobs, matching
│   │   └── main.py       FastAPI app factory
│   ├── tests/            offline pytest suite (no API key needed)
│   └── requirements.txt
├── frontend/             React + Vite + TypeScript match workspace
├── data/taxonomy/        curated skill seed (ESCO-mergeable)
├── scripts/ingest_esco.py
├── docker-compose.yml    backend (+ optional local Ollama profile)
└── Makefile
```

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Then pick a provider in `.env`:

**Option A — NVIDIA NIM (brief default, free dev credits)**
```ini
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-...        # free key from https://build.nvidia.com
NVIDIA_CHAT_MODEL=meta/llama-3.1-8b-instruct
```

**Option B — Local Ollama (free, unlimited, private)**
```bash
# install Ollama from https://ollama.com, then:
ollama pull llama3.1:8b
```
```ini
LLM_PROVIDER=openai_compatible
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_CHAT_MODEL=llama3.1:8b
```

Run it:
```bash
uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api -> :8000)
```

Open the app, click **Load sample**, then **Run explainable match**.

### 3. Tests (no API key required)

```bash
cd backend
python -m pytest
```

---

## Using the full ESCO taxonomy (real data, ~13.9k skills)

The seed taxonomy covers the most common tech/business skills. To normalize
against the authoritative EU reference vocabulary:

1. Download the free ESCO classification CSV (your language) from
   <https://esco.ec.europa.eu/en/use-esco/download> (you must accept the
   licence) → you'll get e.g. `skills_en.csv`.
2. Convert it to the merge format:
   ```bash
   python scripts/ingest_esco.py /path/to/skills_en.csv --out data/taxonomy/esco_skills.csv
   ```
3. Point the backend at it in `.env`:
   ```ini
   ESCO_SKILLS_CSV=data/taxonomy/esco_skills.csv
   ```
Your curated seed always wins on ID collisions, so hand-tuned aliases are kept
while ESCO fills the long tail.

> **Real model datasets.** If/when a module fine-tunes or evaluates a model,
> use real corpora rather than synthetic toys — e.g. Kaggle resume datasets,
> public job-posting datasets, and the ESCO occupation↔skill relations above.
> No training is required for this foundation module (it's retrieval + LLM
> extraction), so we ship the real taxonomy instead.

---

## API surface (Iteration 1)

| Method | Path                      | Purpose                                              |
|-------:|---------------------------|------------------------------------------------------|
| GET    | `/health`                 | Status, active provider/model, taxonomy size         |
| POST   | `/documents/extract-text` | Read a PDF / Word / image into text (offline OCR)    |
| POST   | `/candidates/text`        | Extract + persist a candidate profile from CV text   |
| POST   | `/candidates/upload`      | Same, from an uploaded PDF / DOCX / TXT             |
| GET    | `/candidates`             | List candidates                                      |
| POST   | `/jobs/text`              | Extract + persist a job profile                      |
| POST   | `/match`                  | Score a stored candidate against a stored job        |
| POST   | `/match/adhoc`            | One-shot: paste CV + job, get explainable result     |
| POST   | `/learning-plan`          | Turn match gaps into a sequenced, resourced learning plan |
| POST   | `/interview/start`        | Generate tailored mock-interview questions               |
| POST   | `/interview/report`       | Grade an answered transcript into a scored debrief       |

Full interactive schema at `/docs`.

### Document upload & offline OCR

Both the CV and job inputs accept **PDF, Word (.docx), and images (PNG/JPG/…)**,
read **entirely offline with no API key**:

* Digital PDFs / Word → fast text extraction (pdfplumber / python-docx).
* Scanned PDFs and images → **RapidOCR** (PaddleOCR's detection/recognition
  models via ONNX Runtime) with a noise-resistance preprocessing pass
  (grayscale, auto-contrast, upscaling). Scanned PDF pages are rendered at
  300 DPI with PyMuPDF before OCR.

The UI uploads the file, shows the extracted text in an **editable** box (so you
can verify/fix OCR output), then runs the normal match. Only the skill-reasoning
step uses the configured LLM; all file reading is local.

---

## Roadmap

The foundation exposes a clean, reusable skill graph + match engine. Remaining
modules from the brief build directly on it:

1. ~~**Adaptive Learning Coach**~~ ✅ **Built** — turns `MatchResult.gaps` into a
   sequenced upskilling roadmap: prioritized skill modules (concepts, steps, a
   portfolio practice project, real resources) plus week-by-week missions.
   See `POST /learning-plan` and the in-app "Generate learning plan" flow.
2. ~~**Interview Simulator**~~ ✅ **Built** — a role-specific mock interview:
   tailored questions from the candidate's strengths + the role's gaps, answered
   one at a time, then a rubric-scored debrief (per-answer feedback, strengths,
   improvements, next steps). See `POST /interview/start` + `/interview/report`.
3. **HR Agent with tools** — a tool-using agent calling live job-market / salary
   APIs to enrich and benchmark match results.
4. **AI Career Twin** — a persisted, evolving profile across learn → practice →
   prove → interview → match, reusing the same trusted evidence base.

---

## Responsible AI

This system **supports** educators and recruiters; it does not replace them.
Every recommendation is traceable to evidence and a transparent score.
The matcher compares on skills and evidence — not school name, gender, age, or
nationality — and rewards adjacent skills to reduce bias against non-traditional
paths. CVs and transcripts are sensitive data: keep `.env` secrets out of
version control, and prefer the local-Ollama provider when data must not leave
your environment.
```
