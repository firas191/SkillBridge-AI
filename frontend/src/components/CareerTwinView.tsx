import type { CareerTwin, TwinActivity } from "../types";

const KIND_LABEL: Record<string, string> = {
  match: "Role match",
  interview: "Interview",
  learning: "Learning plan",
};

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleDateString();
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="twin-stat">
      <b>{value}</b>
      <span>{label}</span>
    </div>
  );
}

function ActivityRow({ a }: { a: TwinActivity }) {
  return (
    <div className="twin-act">
      <span className={`twin-act-kind k-${a.kind}`}>{KIND_LABEL[a.kind] || a.kind}</span>
      <span className="twin-act-title">{a.title || "—"}</span>
      <span className="twin-act-meta">
        {a.score != null && <b>{Math.round(a.score)}</b>}
        <span className="twin-act-date">{fmtDate(a.created_at)}</span>
      </span>
    </div>
  );
}

export default function CareerTwinView({ twin }: { twin: CareerTwin }) {
  const ag = twin.aggregate;
  const b = twin.briefing;
  return (
    <div className="twin">
      <div className="card twin-hero">
        <div className="twin-hero-top">
          <div>
            <div className="plan-kicker">Living career profile</div>
            <h3 className="twin-name">{twin.name}</h3>
          </div>
          <div className="twin-stats">
            <Stat label="roles explored" value={String(ag.roles_explored)} />
            {ag.best_fit_score != null && (
              <Stat label="best fit" value={`${Math.round(ag.best_fit_score)}`} />
            )}
            <Stat label="interviews" value={String(ag.interviews_taken)} />
            <Stat label="plans" value={String(ag.learning_plans)} />
          </div>
        </div>

        {b.headline && <p className="twin-headline">{b.headline}</p>}
        {b.narrative && <p className="twin-narrative">{b.narrative}</p>}
        {(b.momentum || b.recommended_direction) && (
          <div className="twin-signals">
            {b.momentum && (
              <div className="twin-signal">
                <span>Momentum</span>
                {b.momentum}
              </div>
            )}
            {b.recommended_direction && (
              <div className="twin-signal">
                <span>Lean into</span>
                {b.recommended_direction}
              </div>
            )}
          </div>
        )}
      </div>

      {b.next_missions.length > 0 && (
        <>
          <div className="section-title">Your next missions</div>
          <div className="priority">
            {b.next_missions.map((m, i) => (
              <span key={i} className="prio">
                <b>{i + 1}</b>
                {m}
              </span>
            ))}
          </div>
        </>
      )}

      {ag.recurring_gaps.length > 0 && (
        <>
          <div className="section-title">Gaps that keep coming up</div>
          <div className="chips">
            {ag.recurring_gaps.map((g, i) => (
              <span key={i} className="chip">
                {g}
              </span>
            ))}
          </div>
        </>
      )}

      <div className="section-title">Activity timeline</div>
      <div className="card twin-timeline">
        {twin.activities.length === 0 && <p className="muted">No activity yet.</p>}
        {twin.activities.map((a) => (
          <ActivityRow key={a.id} a={a} />
        ))}
      </div>
    </div>
  );
}
