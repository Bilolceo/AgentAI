"use client";

// Lightweight, dependency-free charts (CSS/SVG) for the manager dashboard.
// Professional clinic look: restrained palette, no animations beyond subtle.
import React from "react";

const PALETTE: Record<string, string> = {
  emerald: "#10b981",
  amber: "#f59e0b",
  blue: "#3b82f6",
  red: "#ef4444",
  slate: "#94a3b8",
  teal: "#14b8a6",
  rose: "#f43f5e",
  orange: "#f97316",
  indigo: "#6366f1",
  violet: "#8b5cf6",
};

export function color(name: string): string {
  return PALETTE[name] ?? name;
}

// Map appointment/call status -> a chart color name.
export function statusColor(status: string): string {
  const map: Record<string, string> = {
    confirmed: "emerald",
    completed: "emerald",
    arrived: "teal",
    in_progress: "indigo",
    pending: "amber",
    new: "blue",
    operator_required: "orange",
    cancelled: "red",
    no_show: "rose",
  };
  return map[status] ?? "slate";
}

export type Segment = { label: string; value: number; color: string };

export function DonutChart({
  segments,
  size = 168,
  thickness = 26,
  centerValue,
  centerLabel,
}: {
  segments: Segment[];
  size?: number;
  thickness?: number;
  centerValue: React.ReactNode;
  centerLabel?: string;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  let acc = 0;
  const stops = segments
    .filter((s) => s.value > 0)
    .map((s) => {
      const start = (acc / (total || 1)) * 100;
      acc += s.value;
      const end = (acc / (total || 1)) * 100;
      return `${color(s.color)} ${start}% ${end}%`;
    })
    .join(", ");
  const bg = total > 0 && stops ? `conic-gradient(${stops})` : "#e2e8f0";
  const inner = size - thickness * 2;

  return (
    <div className="flex flex-wrap items-center gap-5">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <div className="rounded-full" style={{ width: size, height: size, background: bg }} />
        <div
          className="absolute flex flex-col items-center justify-center rounded-full bg-white shadow-inner"
          style={{ width: inner, height: inner, top: thickness, left: thickness }}
        >
          <div className="text-3xl font-semibold text-slate-900">{centerValue}</div>
          {centerLabel ? <div className="mt-0.5 text-xs text-slate-500">{centerLabel}</div> : null}
        </div>
      </div>
      <ul className="min-w-[140px] space-y-1.5 text-sm">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color(s.color) }} />
            <span className="text-slate-600">{s.label}</span>
            <span className="ml-auto font-semibold text-slate-800">{s.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function HBars({
  items,
  barColor = "blue",
}: {
  items: { label: string; value: number; sub?: string }[];
  barColor?: string;
}) {
  const max = Math.max(1, ...items.map((i) => i.value));
  return (
    <div className="space-y-3">
      {items.map((i) => (
        <div key={i.label}>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-slate-700">
              {i.label}
              {i.sub ? <span className="ml-1 text-slate-400">{i.sub}</span> : null}
            </span>
            <span className="font-semibold text-slate-800">{i.value}</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-2.5 rounded-full"
              style={{ width: `${(i.value / max) * 100}%`, background: color(barColor) }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// A richer KPI tile with a colored accent bar (professional, scannable).
export function StatTile({
  label,
  value,
  accent = "blue",
  caption,
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  accent?: string;
  caption?: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="h-1" style={{ background: color(accent) }} />
      <div className="p-4">
        <div className="text-3xl font-semibold text-slate-900">{value}</div>
        <div className="mt-1 text-xs font-medium text-slate-500">{label}</div>
        {caption ? <div className="mt-1 text-[11px] text-slate-400">{caption}</div> : null}
      </div>
    </div>
  );
}
