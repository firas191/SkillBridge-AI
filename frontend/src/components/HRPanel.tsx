import { useState } from "react";
import { getHrRecommendation } from "../api";
import type { HRRecommendation, HRRequest } from "../types";

interface Props {
  candidateName: string;
  jobTitle: string;
  strengths: string[];
  gaps: string[];
  overallScore: number;
  verdict?: string;
  summary?: string;
}

const DECISION_CLASS: Record<string, string> = {
  advance: "v-strong",
  interview_with_focus: "v-moderate",
  hold: "v-moderate",
  not_yet: "v-weak",
};

const DEMAND_LABEL: Record<string, string> = {
  very_high: "very high",
  high: "high",
  moderate: "moderate",
  niche: "niche",
};

function money(n: number, currency: string): string {
  return `${currency} ${n.toLocaleString()}`;
}

export default function HRPanel(props: Props) {
  const [phase, setPhase] = useState<"idle" | "loading" | "result">("idle");
  const [rec, setRec] = useState<HRRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setError(null);
    setPhase("loading");
    try {
      const payload: HRRequest = {
        candidate_name: props.candidateName,
        job_title: props.jobTitle,
        strengths: props.strengths,
        gaps: props.gaps,
        overall_score: props.overallScore,
        verdict: props.verdict,
        summary: props.summary,
      };
      setRec(await getHrRecommendation(payload));
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate brief");
      setPhase("idle");
    }
  }

  if (phase === "idle") {
    return (
      <div className="card iv-start">
        <div>
          <h3>Generate a recruiter brief</h3>
          <p className="hint">
            The agent gathers live market evidence — salary benchmark, skill demand,
            outlook — and weighs it into an advisory hiring recommendation. Decision
            support only; a human decides.
          </p>
        </div>
        <div className="iv-start-actions">
          <button className="btn-primary" onClick={generate}>
            Generate recruiter brief
          </button>
        </div>
        {error && <p className="doc-error" style={{ width: "100%" }}>{error}</p>}
      </div>
    );
  }

  if (phase === "loading") {
    return (
      <div className="card iv-loading">
        <span className="spinner spinner-dark" /> Consulting market tools…
      </div>
    );
  }

  if (phase === "result" && rec) {
    const dClass = DECISION_CLASS[rec.decision] || "v-moderate";
    const s = rec.salary_benchmark;
    return (
      <div className="hr">
        <div className="card hr-head">
          <span className={`verdict ${dClass}`}>{rec.decision_label}</span>
          <h3 className="hr-headline">{rec.headline}</h3>
          <p className="summary">{rec.rationale}</p>

          <div className="hr-metrics">
            {s && (
              <div className="hr-metric">
                <div className="hr-metric-label">Market salary · {s.seniority}</div>
                <div className="hr-metric-value">
                  {money(s.min, s.currency)} – {money(s.max, s.currency)}
                </div>
                <div className="hr-metric-sub">median {money(s.median, s.currency)}</div>
              </div>
            )}
            {rec.market_outlook && (
              <div className="hr-metric hr-metric-wide">
                <div className="hr-metric-label">Market outlook</div>
                <div className="hr-metric-sub">{rec.market_outlook}</div>
              </div>
            )}
          </div>
        </div>

        {rec.skill_demand.length > 0 && (
          <>
            <div className="section-title">Skill demand</div>
            <div className="chips">
              {rec.skill_demand.map((d, i) => (
                <span key={i} className={`chip demand demand-${d.demand}`}>
                  {d.skill}
                  <em>{DEMAND_LABEL[d.demand] || d.demand}</em>
                </span>
              ))}
            </div>
          </>
        )}

        <div className="iv-cols" style={{ marginTop: 8 }}>
          {rec.interview_focus.length > 0 && (
            <div>
              <div className="section-title">Interview focus</div>
              <ul className="iv-list">
                {rec.interview_focus.map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
          )}
          {rec.risks.length > 0 && (
            <div>
              <div className="section-title">Risks &amp; open questions</div>
              <ul className="iv-list">
                {rec.risks.map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {rec.fairness_notes.length > 0 && (
          <div className="hr-fair">
            <div className="hr-fair-label">Responsible hiring</div>
            <ul>
              {rec.fairness_notes.map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ul>
          </div>
        )}

        <details className="hr-tools">
          <summary>Evidence the agent used ({rec.tool_calls.length} tools)</summary>
          {rec.tool_calls.map((t, i) => (
            <div key={i} className="hr-tool">
              <span className="hr-tool-name">{t.tool}</span>
              <span className="hr-tool-summary">{t.summary}</span>
              {t.source && <span className="hr-tool-src">{t.source}</span>}
            </div>
          ))}
        </details>

        <p className="hr-disclaimer">{rec.disclaimer}</p>

        <button className="btn-ghost" onClick={() => setPhase("idle")}>
          Regenerate
        </button>
      </div>
    );
  }

  return null;
}
