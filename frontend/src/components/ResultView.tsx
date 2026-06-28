import type { AdhocMatchResponse, SkillMatch } from "../types";
import ScoreGauge from "./ScoreGauge";

const VERDICT_LABEL: Record<string, string> = {
  strong_fit: "Strong fit",
  moderate_fit: "Moderate fit",
  weak_fit: "Weak fit",
};
const VERDICT_CLASS: Record<string, string> = {
  strong_fit: "v-strong",
  moderate_fit: "v-moderate",
  weak_fit: "v-weak",
};
const STATUS_CLASS: Record<string, string> = {
  matched: "p-matched",
  partial: "p-partial",
  missing: "p-missing",
};

function SkillCard({ m }: { m: SkillMatch }) {
  return (
    <div className="skill">
      <div className="skhead">
        <span className="name">{m.requirement}</span>
        <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="tag">{m.importance.replace(/_/g, " ")}</span>
          <span className={`pill ${STATUS_CLASS[m.status]}`}>{m.status}</span>
        </span>
      </div>
      <p className="rationale">{m.rationale}</p>
      {m.candidate_evidence && <p className="evidence">“{m.candidate_evidence}”</p>}
    </div>
  );
}

export default function ResultView({ data }: { data: AdhocMatchResponse }) {
  const { result, candidate, job } = data;
  const partials = result.matched_skills.filter((m) => m.status === "partial");
  const fullMatches = result.matched_skills.filter((m) => m.status === "matched");

  return (
    <div className="result">
      <div className="card">
        <div className="score-row">
          <ScoreGauge score={result.overall_score} />
          <div style={{ flex: 1, minWidth: 240 }}>
            <span className={`verdict ${VERDICT_CLASS[result.verdict]}`}>
              {VERDICT_LABEL[result.verdict]}
            </span>
            <p className="summary">{result.summary}</p>
            <p className="muted" style={{ marginTop: 8 }}>
              {candidate.name} → {job.title}
            </p>
          </div>
          <div className="bars">
            <Bar label="Required coverage" value={result.required_coverage} />
            <Bar label="Preferred coverage" value={result.preferred_coverage} />
          </div>
        </div>
      </div>

      {fullMatches.length > 0 && (
        <>
          <div className="section-title">Matched skills ({fullMatches.length})</div>
          {fullMatches.map((m, i) => (
            <SkillCard key={`f${i}`} m={m} />
          ))}
        </>
      )}

      {partials.length > 0 && (
        <>
          <div className="section-title">Partial matches ({partials.length})</div>
          {partials.map((m, i) => (
            <SkillCard key={`p${i}`} m={m} />
          ))}
        </>
      )}

      {result.missing_skills.length > 0 && (
        <>
          <div className="section-title">Missing skills ({result.missing_skills.length})</div>
          {result.missing_skills.map((m, i) => (
            <SkillCard key={`m${i}`} m={m} />
          ))}
        </>
      )}

      {result.gaps.length > 0 && (
        <>
          <div className="section-title">Gap plan</div>
          {result.gaps.map((g, i) => (
            <div key={`g${i}`} className={`gap ${g.severity}`}>
              <div className="g-skill">
                {g.skill} <span className="tag">{g.severity}</span>
              </div>
              <div className="g-rec">{g.recommendation}</div>
            </div>
          ))}
        </>
      )}

      {result.extra_skills.length > 0 && (
        <>
          <div className="section-title">Extra strengths beyond the role</div>
          <div className="chips">
            {result.extra_skills.map((s, i) => (
              <span key={`e${i}`} className="chip">
                {s}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="bar-item">
      <div className="top">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="bar">
        <span style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
