interface Props {
  score: number; // 0..100
}

function colorFor(score: number): string {
  if (score >= 75) return "#2e6b4f"; // forest
  if (score >= 50) return "#966f1c"; // ochre
  return "#a3392b"; // brick
}

export default function ScoreGauge({ score }: Props) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);
  const color = colorFor(clamped);

  return (
    <div className="gauge">
      <svg width="132" height="132" viewBox="0 0 132 132">
        <circle cx="66" cy="66" r={radius} fill="none" stroke="#e2dccf" strokeWidth="9" />
        <circle
          cx="66"
          cy="66"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 66 66)"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="label">
        <div>
          <div className="num" style={{ color }}>
            {Math.round(clamped)}
          </div>
          <div className="of">/ 100 match</div>
        </div>
      </div>
    </div>
  );
}
