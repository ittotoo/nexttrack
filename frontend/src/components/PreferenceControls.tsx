import { useState } from "react";

export interface Preferences {
  diversity_weight: number;
  target_energy: number | undefined;
  target_valence: number | undefined;
  target_danceability: number | undefined;
  limit: number;
}

interface PreferenceControlsProps {
  value: Preferences;
  onChange: (prefs: Preferences) => void;
}

interface SliderProps {
  id: string;
  label: string;
  lowLabel: string;
  highLabel: string;
  value: number | undefined;
  defaultVal: number;
  enabled: boolean;
  onToggle: (on: boolean) => void;
  onValue: (v: number) => void;
}

function Slider({
  id,
  label,
  lowLabel,
  highLabel,
  value,
  defaultVal,
  enabled,
  onToggle,
  onValue,
}: SliderProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-sm font-medium text-gray-700">
          {label}
        </label>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-8 text-right tabular-nums">
            {enabled ? (value ?? defaultVal).toFixed(1) : "—"}
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            onClick={() => onToggle(!enabled)}
            className={`relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors ${
              enabled ? "bg-brand-600" : "bg-gray-300"
            }`}
            aria-label={`Toggle ${label}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform mt-0.5 ${
                enabled ? "translate-x-4 ml-0.5" : "translate-x-0.5"
              }`}
            />
          </button>
        </div>
      </div>
      <input
        id={id}
        type="range"
        min={0}
        max={1}
        step={0.1}
        value={value ?? defaultVal}
        disabled={!enabled}
        onChange={(e) => onValue(parseFloat(e.target.value))}
        className="w-full accent-brand-600 disabled:opacity-40"
      />
      <div className="flex justify-between text-xs text-gray-400">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  );
}

export default function PreferenceControls({
  value,
  onChange,
}: PreferenceControlsProps) {
  const [expanded, setExpanded] = useState(false);

  const update = (patch: Partial<Preferences>) =>
    onChange({ ...value, ...patch });

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-gray-700"
        aria-expanded={expanded}
      >
        <span>Preferences</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
        >
          <path
            fillRule="evenodd"
            d="M5.22 8.22a.75.75 0 011.06 0L10 11.94l3.72-3.72a.75.75 0 111.06 1.06l-4.25 4.25a.75.75 0 01-1.06 0L5.22 9.28a.75.75 0 010-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-gray-200 px-4 py-4 space-y-5">
          {/* Diversity is always enabled */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label
                htmlFor="diversity"
                className="text-sm font-medium text-gray-700"
              >
                Diversity
              </label>
              <span className="text-xs text-gray-500 tabular-nums">
                {value.diversity_weight.toFixed(1)}
              </span>
            </div>
            <input
              id="diversity"
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={value.diversity_weight}
              onChange={(e) =>
                update({ diversity_weight: parseFloat(e.target.value) })
              }
              className="w-full accent-brand-600"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Similar</span>
              <span>Diverse</span>
            </div>
          </div>

          <Slider
            id="energy"
            label="Energy"
            lowLabel="Calm"
            highLabel="Energetic"
            value={value.target_energy}
            defaultVal={0.5}
            enabled={value.target_energy !== undefined}
            onToggle={(on) =>
              update({ target_energy: on ? 0.5 : undefined })
            }
            onValue={(v) => update({ target_energy: v })}
          />
          <Slider
            id="valence"
            label="Mood"
            lowLabel="Melancholic"
            highLabel="Happy"
            value={value.target_valence}
            defaultVal={0.5}
            enabled={value.target_valence !== undefined}
            onToggle={(on) =>
              update({ target_valence: on ? 0.5 : undefined })
            }
            onValue={(v) => update({ target_valence: v })}
          />
          <Slider
            id="danceability"
            label="Danceability"
            lowLabel="Chill"
            highLabel="Dance"
            value={value.target_danceability}
            defaultVal={0.5}
            enabled={value.target_danceability !== undefined}
            onToggle={(on) =>
              update({ target_danceability: on ? 0.5 : undefined })
            }
            onValue={(v) => update({ target_danceability: v })}
          />

          <div className="space-y-1">
            <label
              htmlFor="limit"
              className="text-sm font-medium text-gray-700"
            >
              Number of results
            </label>
            <select
              id="limit"
              value={value.limit}
              onChange={(e) => update({ limit: parseInt(e.target.value, 10) })}
              className="block w-full rounded border border-gray-300 px-3 py-1.5 text-sm"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
