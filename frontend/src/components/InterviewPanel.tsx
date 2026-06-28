import { useState } from "react";
import { getInterviewReport, startInterview } from "../api";
import type {
  InterviewPlan,
  InterviewPlanRequest,
  InterviewReport,
} from "../types";
import ScoreGauge from "./ScoreGauge";

interface Props {
  candidateName: string;
  jobTitle: string;
  strengths: string[];
  gaps: string[];
  summary?: string;
  onReport?: (report: InterviewReport) => void;
}

type Phase = "idle" | "loadingPlan" | "interviewing" | "loadingReport" | "report";

function msg(e: unknown): string {
  return e instanceof Error ? e.message : "Something went wrong";
}

export default function InterviewPanel(props: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [plan, setPlan] = useState<InterviewPlan | null>(null);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [numQuestions, setNumQuestions] = useState(5);

  async function start() {
    setError(null);
    setReport(null);
    setPhase("loadingPlan");
    try {
      const payload: InterviewPlanRequest = {
        candidate_name: props.candidateName,
        job_title: props.jobTitle,
        summary: props.summary,
        strengths: props.strengths,
        gaps: props.gaps,
        num_questions: numQuestions,
      };
      const p = await startInterview(payload);
      if (!p.questions.length) throw new Error("No questions were generated — try again.");
      setPlan(p);
      setAnswers(new Array(p.questions.length).fill(""));
      setIdx(0);
      setPhase("interviewing");
    } catch (e) {
      setError(msg(e));
      setPhase("idle");
    }
  }

  function setAnswer(v: string) {
    setAnswers((a) => {
      const c = [...a];
      c[idx] = v;
      return c;
    });
  }

  async function finish() {
    if (!plan) return;
    setError(null);
    setPhase("loadingReport");
    try {
      const transcript = plan.questions.map((q, i) => ({
        question: q.question,
        focus: q.focus,
        what_good_looks_like: q.what_good_looks_like,
        answer: answers[i] || "",
      }));
      const r = await getInterviewReport({
        candidate_name: props.candidateName,
        job_title: props.jobTitle,
        transcript,
      });
      setReport(r);
      setPhase("report");
      props.onReport?.(r);
    } catch (e) {
      setError(msg(e));
      setPhase("interviewing");
    }
  }

  function reset() {
    setPhase("idle");
    setPlan(null);
    setReport(null);
    setIdx(0);
    setAnswers([]);
    setError(null);
  }

  // ---- idle ----
  if (phase === "idle") {
    return (
      <div className="card iv-start">
        <div>
          <h3>Practice a mock interview</h3>
          <p className="hint">
            Role-specific questions drawn from your strengths and the gaps for this
            role. Answer them, then get a scored, honest debrief.
          </p>
        </div>
        <div className="iv-start-actions">
          <label className="hours-sel">
            Questions
            <select
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
            >
              {[3, 4, 5, 6, 8].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <button className="btn-primary" onClick={start}>
            Start mock interview
          </button>
        </div>
        {error && <p className="doc-error" style={{ width: "100%" }}>{error}</p>}
      </div>
    );
  }

  // ---- loading ----
  if (phase === "loadingPlan" || phase === "loadingReport") {
    return (
      <div className="card iv-loading">
        <span className="spinner spinner-dark" />
        {phase === "loadingPlan" ? "Preparing your interview…" : "Scoring your answers…"}
      </div>
    );
  }

  // ---- interviewing ----
  if (phase === "interviewing" && plan) {
    const q = plan.questions[idx];
    const last = idx === plan.questions.length - 1;
    return (
      <div className="card iv-room">
        <div className="iv-top">
          <span className="iv-progress">
            Question {idx + 1} of {plan.questions.length}
          </span>
          <span className="tag">{q.focus}</span>
        </div>
        {idx === 0 && plan.intro && <p className="iv-intro">{plan.intro}</p>}
        <div className="iv-question">{q.question}</div>
        <textarea
          className="iv-answer"
          value={answers[idx] || ""}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Type your answer as you would say it in the interview…"
        />
        {error && <p className="doc-error">{error}</p>}
        <div className="iv-nav">
          <button
            className="btn-ghost"
            onClick={() => setIdx(idx - 1)}
            disabled={idx === 0}
          >
            ← Back
          </button>
          {last ? (
            <button className="btn-primary" onClick={finish}>
              Finish &amp; get feedback
            </button>
          ) : (
            <button className="btn-primary" onClick={() => setIdx(idx + 1)}>
              Next question →
            </button>
          )}
        </div>
      </div>
    );
  }

  // ---- report ----
  if (phase === "report" && report) {
    const verdictClass =
      report.overall_score >= 75
        ? "v-strong"
        : report.overall_score >= 50
          ? "v-moderate"
          : "v-weak";
    return (
      <div className="iv-report">
        <div className="card">
          <div className="score-row">
            <ScoreGauge score={report.overall_score} />
            <div style={{ flex: 1, minWidth: 240 }}>
              <span className={`verdict ${verdictClass}`}>{report.verdict}</span>
              <p className="summary">{report.summary}</p>
            </div>
          </div>
        </div>

        <div className="section-title">Answer-by-answer feedback</div>
        {report.assessments.map((a, i) => (
          <div key={i} className="skill iv-assess">
            <div className="skhead">
              <span className="name">{a.question}</span>
              <span className="iv-grade">{a.score}/5</span>
            </div>
            <p className="rationale">{a.feedback}</p>
            {a.strong_answer_points.length > 0 && (
              <ul className="iv-points">
                {a.strong_answer_points.map((p, j) => (
                  <li key={j}>{p}</li>
                ))}
              </ul>
            )}
          </div>
        ))}

        <div className="iv-cols">
          {report.strengths.length > 0 && (
            <div>
              <div className="section-title">What you did well</div>
              <ul className="iv-list">
                {report.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {report.improvements.length > 0 && (
            <div>
              <div className="section-title">Work on this</div>
              <ul className="iv-list">
                {report.improvements.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {report.next_steps.length > 0 && (
          <>
            <div className="section-title">Next steps</div>
            <ul className="iv-list">
              {report.next_steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </>
        )}

        <div style={{ marginTop: 18 }}>
          <button className="btn-ghost" onClick={reset}>
            Practice again
          </button>
        </div>
      </div>
    );
  }

  return null;
}
