import { useEffect, useRef, useState } from "react";
import {
  adhocMatch,
  extractDocText,
  generateLearningPlan,
  getTwin,
  saveToTwin,
} from "./api";
import type {
  AdhocMatchResponse,
  CareerTwin,
  InterviewReport,
  LearningPlan,
  LearningPlanRequest,
  TwinSaveRequest,
} from "./types";
import ResultView from "./components/ResultView";
import LearningPlanView from "./components/LearningPlanView";
import InterviewPanel from "./components/InterviewPanel";
import HRPanel from "./components/HRPanel";
import CareerTwinView from "./components/CareerTwinView";
import Logo from "./components/Logo";

function candidateStrengths(d: AdhocMatchResponse): string[] {
  const s = new Set<string>();
  d.result.matched_skills.forEach((m) => s.add(m.candidate_skill || m.requirement));
  d.result.extra_skills.forEach((x) => s.add(x));
  return Array.from(s).slice(0, 25);
}

function buildPlanRequest(d: AdhocMatchResponse, hours: number): LearningPlanRequest {
  const r = d.result;
  return {
    candidate_name: r.candidate_name || d.candidate.name || "Candidate",
    job_title: r.job_title || d.job.title || "the role",
    gaps: r.gaps.map((g) => ({
      skill: g.skill,
      importance: g.importance,
      severity: g.severity,
    })),
    strengths: candidateStrengths(d),
    weekly_hours: hours,
  };
}

const ACCEPT = ".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff,image/*";

const METHOD_LABEL: Record<string, string> = {
  "pdf-text": "PDF",
  "pdf-ocr": "PDF",
  docx: "Word",
  text: "Text",
  "image-ocr": "Image",
};

interface DocMeta {
  filename: string;
  method: string;
}

interface SourceCardProps {
  title: string;
  hint: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  onFile: (f: File) => void;
  onRemove: () => void;
  busy: boolean;
  disabled: boolean;
  meta: DocMeta | null;
  error: string | null;
}

function SourceCard(props: SourceCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <h2>{props.title}</h2>
          <p className="hint">{props.hint}</p>
        </div>
        <button
          className="btn-ghost btn-sm"
          onClick={() => inputRef.current?.click()}
          disabled={props.busy || props.disabled}
          title="Upload a PDF, Word file, or image"
        >
          {props.busy ? (
            <>
              <span className="spinner spinner-dark" />
              &nbsp;Uploading…
            </>
          ) : props.meta ? (
            "Replace"
          ) : (
            "⬆ Upload file"
          )}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) props.onFile(f);
            e.target.value = ""; // allow re-uploading the same file
          }}
        />
      </div>

      {props.meta ? (
        <div className="filecard">
          <span className="filecard-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
            </svg>
          </span>
          <div className="filecard-info">
            <div className="filecard-name">{props.meta.filename}</div>
            <div className="filecard-sub">
              Uploaded <span className="badge">{METHOD_LABEL[props.meta.method] || "File"}</span>
            </div>
          </div>
          <button
            className="filecard-remove"
            onClick={props.onRemove}
            title="Remove file"
            aria-label="Remove file"
          >
            ×
          </button>
        </div>
      ) : (
        <textarea
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder={props.placeholder}
        />
      )}

      {props.error && <p className="doc-error">{props.error}</p>}
    </div>
  );
}

export default function App() {
  const [cv, setCv] = useState("");
  const [job, setJob] = useState("");
  const [cvMeta, setCvMeta] = useState<DocMeta | null>(null);
  const [jobMeta, setJobMeta] = useState<DocMeta | null>(null);
  // Text extracted from an uploaded file, kept off-screen (not shown in the box).
  const [cvDocText, setCvDocText] = useState("");
  const [jobDocText, setJobDocText] = useState("");
  const [cvBusy, setCvBusy] = useState(false);
  const [jobBusy, setJobBusy] = useState(false);
  const [cvErr, setCvErr] = useState<string | null>(null);
  const [jobErr, setJobErr] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AdhocMatchResponse | null>(null);

  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planErr, setPlanErr] = useState<string | null>(null);
  const [weeklyHours, setWeeklyHours] = useState(8);

  const [twin, setTwin] = useState<CareerTwin | null>(null);
  const [twinId, setTwinId] = useState<string | null>(() => {
    try {
      return localStorage.getItem("skillbridge_twin_id");
    } catch {
      return null;
    }
  });
  const [twinSaving, setTwinSaving] = useState(false);
  const [twinErr, setTwinErr] = useState<string | null>(null);

  useEffect(() => {
    if (twinId) getTwin(twinId).then(setTwin).catch(() => setTwin(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshTwin(id: string) {
    try {
      setTwin(await getTwin(id));
    } catch {
      /* ignore */
    }
  }

  async function saveTwinActivity(
    kind: string,
    title: string,
    score: number | null,
    verdict: string | null,
    detail: Record<string, unknown>,
  ) {
    if (!data) return;
    setTwinErr(null);
    setTwinSaving(true);
    try {
      const payload: TwinSaveRequest = {
        candidate_name: data.result.candidate_name || data.candidate.name || "Candidate",
        profile: data.candidate,
        kind,
        title,
        score,
        verdict,
        detail,
      };
      const res = await saveToTwin(payload);
      setTwinId(res.twin_id);
      try {
        localStorage.setItem("skillbridge_twin_id", res.twin_id);
      } catch {
        /* ignore */
      }
      await refreshTwin(res.twin_id);
    } catch (e) {
      setTwinErr(e instanceof Error ? e.message : "Could not save to Career Twin");
    } finally {
      setTwinSaving(false);
    }
  }

  function saveMatchToTwin() {
    if (!data) return;
    const r = data.result;
    saveTwinActivity("match", r.job_title || "the role", r.overall_score, r.verdict, {
      gaps: r.gaps.map((g) => g.skill),
      summary: r.summary,
    });
  }

  async function handleFile(file: File, which: "cv" | "job") {
    const setBusy = which === "cv" ? setCvBusy : setJobBusy;
    const setErr = which === "cv" ? setCvErr : setJobErr;
    const setDocText = which === "cv" ? setCvDocText : setJobDocText;
    const setMeta = which === "cv" ? setCvMeta : setJobMeta;
    setErr(null);
    setBusy(true);
    try {
      // Read the file silently — its text powers the match but is never shown.
      const doc = await extractDocText(file);
      setDocText(doc.text);
      setMeta({ filename: doc.filename, method: doc.method });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not read file");
      setMeta(null);
    } finally {
      setBusy(false);
    }
  }

  function removeFile(which: "cv" | "job") {
    if (which === "cv") {
      setCvMeta(null);
      setCvDocText("");
      setCvErr(null);
    } else {
      setJobMeta(null);
      setJobDocText("");
      setJobErr(null);
    }
  }

  async function runMatch() {
    setError(null);
    setData(null);
    setPlan(null);
    setPlanErr(null);
    setLoading(true);
    try {
      const cvContent = cvMeta ? cvDocText : cv;
      const jobContent = jobMeta ? jobDocText : job;
      setData(await adhocMatch(cvContent, jobContent));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function runPlan() {
    if (!data) return;
    setPlanErr(null);
    setPlan(null);
    setPlanLoading(true);
    try {
      const p = await generateLearningPlan(buildPlanRequest(data, weeklyHours));
      setPlan(p);
      if (twinId) {
        saveTwinActivity("learning", data.result.job_title || "the role", null, null, {
          weeks: p.total_weeks,
          modules: p.modules.length,
        });
      }
    } catch (e) {
      setPlanErr(e instanceof Error ? e.message : "Failed to generate plan");
    } finally {
      setPlanLoading(false);
    }
  }

  const cvReady = cvMeta ? cvDocText.trim().length >= 20 : cv.trim().length >= 20;
  const jobReady = jobMeta ? jobDocText.trim().length >= 20 : job.trim().length >= 20;
  const canSubmit = cvReady && jobReady && !loading && !cvBusy && !jobBusy;

  return (
    <div className="page">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <Logo size={34} />
            <span className="wordmark">
              Skill<em>Bridge</em>
            </span>
          </div>
        </div>
      </header>

      <main className="app">
        <div className="masthead">
          <div className="eyebrow">Skill matching, made clear</div>
          <h1>
            The distance between a résumé and a <span className="it">role</span>,
            measured.
          </h1>
          <p className="lede">
            SkillBridge reads a CV and a job description, finds the skills behind
            both, scores how well they fit — and turns every gap into a plan to
            close it.
          </p>
          <div className="mast-notes">
            <div className="mast-note">
              <b>Backed by proof</b>Every match points to the exact line that shows it.
            </div>
            <div className="mast-note">
              <b>Reads your files</b>Drop in a PDF, Word doc, or a photo of a résumé.
            </div>
            <div className="mast-note">
              <b>Actionable</b>Turns the gaps into a personalized learning plan.
            </div>
          </div>
        </div>

        <div className="sec">
          <span className="sec-n">01</span>
          <span className="sec-t">Inputs</span>
          <span className="sec-rule" />
        </div>

      <div className="grid">
        <SourceCard
          title="Candidate CV"
          hint="Paste the text, or upload a PDF, Word file, or image."
          placeholder="Paste the candidate's CV / resume text here…"
          value={cv}
          onChange={(v) => setCv(v)}
          onFile={(f) => handleFile(f, "cv")}
          onRemove={() => removeFile("cv")}
          busy={cvBusy}
          disabled={loading}
          meta={cvMeta}
          error={cvErr}
        />
        <SourceCard
          title="Job description"
          hint="Paste the text, or upload a PDF, Word file, or image."
          placeholder="Paste the job description here…"
          value={job}
          onChange={(v) => setJob(v)}
          onFile={(f) => handleFile(f, "job")}
          onRemove={() => removeFile("job")}
          busy={jobBusy}
          disabled={loading}
          meta={jobMeta}
          error={jobErr}
        />
      </div>

      <div className="actions">
        <button className="btn-primary" onClick={runMatch} disabled={!canSubmit}>
          {loading ? (
            <>
              <span className="spinner" /> &nbsp;Analyzing…
            </>
          ) : (
            "Run explainable match"
          )}
        </button>
        {(cv || job || cvMeta || jobMeta) && (
          <button
            className="btn-ghost"
            onClick={() => {
              setCv("");
              setJob("");
              setData(null);
              setError(null);
              setCvMeta(null);
              setJobMeta(null);
              setCvDocText("");
              setJobDocText("");
              setCvErr(null);
              setJobErr(null);
              setPlan(null);
              setPlanErr(null);
            }}
            disabled={loading}
          >
            Clear
          </button>
        )}
      </div>

      {error && (
        <p className="error" style={{ marginTop: 16 }}>
          {error}
        </p>
      )}

      {data && (
        <div className="sec">
          <span className="sec-n">02</span>
          <span className="sec-t">Assessment</span>
          <span className="sec-rule" />
        </div>
      )}
      {data && <ResultView data={data} />}

      {data && (
        <div className="twin-save">
          <button className="btn-ghost btn-sm" onClick={saveMatchToTwin} disabled={twinSaving}>
            {twinSaving ? "Saving…" : twin ? "↑ Update Career Twin" : "↑ Save to Career Twin"}
          </button>
          <span className="muted">Build a living profile across every role you check.</span>
          {twinErr && <span className="doc-error">{twinErr}</span>}
        </div>
      )}

      {data && (
        <div className="sec">
          <span className="sec-n">03</span>
          <span className="sec-t">Development plan</span>
          <span className="sec-rule" />
        </div>
      )}
      {data && (
        <div className="card plan-cta">
          <div>
            <h3>Turn these gaps into a learning plan</h3>
            <p className="hint">
              A sequenced roadmap with practice projects, real resources, and weekly missions.
            </p>
          </div>
          <div className="plan-cta-actions">
            <label className="hours-sel">
              Hours/week
              <select
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(Number(e.target.value))}
                disabled={planLoading}
              >
                {[4, 6, 8, 10, 15, 20].map((h) => (
                  <option key={h} value={h}>
                    {h} h
                  </option>
                ))}
              </select>
            </label>
            <button className="btn-primary" onClick={runPlan} disabled={planLoading}>
              {planLoading ? (
                <>
                  <span className="spinner" /> &nbsp;Designing…
                </>
              ) : (
                "Generate learning plan"
              )}
            </button>
          </div>
        </div>
      )}

      {planErr && (
        <p className="error" style={{ marginTop: 16 }}>
          {planErr}
        </p>
      )}

      {plan && <LearningPlanView plan={plan} />}

      {data && (
        <div className="sec">
          <span className="sec-n">04</span>
          <span className="sec-t">Interview practice</span>
          <span className="sec-rule" />
        </div>
      )}
      {data && (
        <InterviewPanel
          candidateName={data.result.candidate_name || data.candidate.name || "Candidate"}
          jobTitle={data.result.job_title || data.job.title || "the role"}
          strengths={candidateStrengths(data)}
          gaps={data.result.gaps.map((g) => g.skill)}
          summary={data.result.summary}
          onReport={(report: InterviewReport) => {
            if (twinId && data)
              saveTwinActivity(
                "interview",
                data.result.job_title || "the role",
                report.overall_score,
                report.verdict,
                {},
              );
          }}
        />
      )}

      {data && (
        <div className="sec">
          <span className="sec-n">05</span>
          <span className="sec-t">Recruiter view</span>
          <span className="sec-rule" />
        </div>
      )}
      {data && (
        <HRPanel
          candidateName={data.result.candidate_name || data.candidate.name || "Candidate"}
          jobTitle={data.result.job_title || data.job.title || "the role"}
          strengths={candidateStrengths(data)}
          gaps={data.result.gaps.map((g) => g.skill)}
          overallScore={data.result.overall_score}
          verdict={data.result.verdict}
          summary={data.result.summary}
        />
      )}

      {twin && (
        <div className="sec">
          <span className="sec-n">06</span>
          <span className="sec-t">Career Twin</span>
          <span className="sec-rule" />
        </div>
      )}
      {twin && <CareerTwinView twin={twin} />}
      </main>
    </div>
  );
}
