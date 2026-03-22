interface ScoreBreakdownProps {
  content: number | null;
  knowledge: number | null;
  popularity: number | null;
}

interface BarProps {
  label: string;
  value: number;
  weight: string;
  color: string;
}

function Bar({ label, value, weight, color }: BarProps) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-600">
          {label}{" "}
          <span className="text-gray-400">({weight})</span>
        </span>
        <span className="tabular-nums font-medium text-gray-700">{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-gray-100">
        <div
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
          role="meter"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${label}: ${pct}%`}
        />
      </div>
    </div>
  );
}

export default function ScoreBreakdown({
  content,
  knowledge,
  popularity,
}: ScoreBreakdownProps) {
  if (content == null && knowledge == null && popularity == null) return null;

  return (
    <div className="space-y-1.5">
      {content != null && (
        <Bar
          label="Audio Similarity"
          value={content}
          weight="40%"
          color="bg-blue-500"
        />
      )}
      {knowledge != null && (
        <Bar
          label="Artist Network"
          value={knowledge}
          weight="30%"
          color="bg-emerald-500"
        />
      )}
      {popularity != null && (
        <Bar
          label="Popularity Match"
          value={popularity}
          weight="30%"
          color="bg-amber-500"
        />
      )}
    </div>
  );
}
