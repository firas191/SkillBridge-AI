import type { LearningPlan, LearningResource } from "../types";

function ResourceLink({ r }: { r: LearningResource }) {
  const inner = (
    <>
      <span className="res-type">{r.type}</span>
      {r.title}
    </>
  );
  return r.url ? (
    <a className="res" href={r.url} target="_blank" rel="noreferrer">
      {inner}
    </a>
  ) : (
    <span className="res res-plain">{inner}</span>
  );
}

export default function LearningPlanView({ plan }: { plan: LearningPlan }) {
  return (
    <div className="plan">
      <div className="card plan-hero">
        <div className="plan-hero-top">
          <div>
            <div className="plan-kicker">PERSONALIZED LEARNING ROADMAP</div>
            <h2 className="plan-title">
              {plan.candidate_name} <span className="arrow">→</span> {plan.job_title}
            </h2>
          </div>
          <div className="plan-stats">
            <div className="stat">
              <b>{plan.total_weeks}</b>
              <span>weeks</span>
            </div>
            <div className="stat">
              <b>{plan.weekly_hours}h</b>
              <span>/ week</span>
            </div>
            <div className="stat">
              <b>{plan.modules.length}</b>
              <span>modules</span>
            </div>
          </div>
        </div>
        {plan.overview && <p className="plan-overview">{plan.overview}</p>}
        {plan.leverage_strengths.length > 0 && (
          <div className="leverage">
            <div className="leverage-title">Leverage your existing strengths</div>
            <ul>
              {plan.leverage_strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {plan.priority_order.length > 0 && (
        <div className="priority">
          {plan.priority_order.map((s, i) => (
            <span key={i} className="prio">
              <b>{i + 1}</b>
              {s}
            </span>
          ))}
        </div>
      )}

      <div className="section-title">Skill modules</div>
      {plan.modules.map((m, i) => (
        <div key={i} className="card module">
          <div className="module-head">
            <span className="module-skill">{m.skill}</span>
            <span className="module-meta">
              <span className="tag">{m.importance.replace(/_/g, " ")}</span>
              {m.estimated_hours > 0 && <span className="hours">{m.estimated_hours}h</span>}
            </span>
          </div>
          {m.why_it_matters && <p className="why">{m.why_it_matters}</p>}
          {m.concepts.length > 0 && (
            <div className="chips">
              {m.concepts.map((c, j) => (
                <span key={j} className="chip">
                  {c}
                </span>
              ))}
            </div>
          )}
          {m.steps.length > 0 && (
            <ol className="steps">
              {m.steps.map((s, j) => (
                <li key={j}>{s}</li>
              ))}
            </ol>
          )}
          {m.practice_project && (
            <div className="project">
              <span className="project-label">Practice project</span>
              {m.practice_project}
            </div>
          )}
          {m.resources.length > 0 && (
            <div className="resources">
              {m.resources.map((r, j) => (
                <ResourceLink key={j} r={r} />
              ))}
            </div>
          )}
        </div>
      ))}

      {plan.weekly_missions.length > 0 && (
        <>
          <div className="section-title">Week-by-week missions</div>
          <div className="missions">
            {plan.weekly_missions.map((w, i) => (
              <div key={i} className="mission">
                <div className="mission-week">W{w.week}</div>
                <div className="mission-body">
                  <div className="mission-theme">
                    {w.theme}
                    {w.focus_skills.length > 0 && (
                      <span className="mission-focus"> · {w.focus_skills.join(", ")}</span>
                    )}
                  </div>
                  {w.tasks.length > 0 && (
                    <ul className="mission-tasks">
                      {w.tasks.map((t, j) => (
                        <li key={j}>{t}</li>
                      ))}
                    </ul>
                  )}
                  {w.deliverable && (
                    <div className="mission-deliv">
                      <span className="deliv-label">Deliverable</span>
                      {w.deliverable}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {plan.closing_note && <p className="closing">{plan.closing_note}</p>}
    </div>
  );
}
