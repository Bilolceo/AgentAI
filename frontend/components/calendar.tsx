"use client";

import React from "react";
import type { ManagerAppointment } from "@/lib/types";
import { color, statusColor } from "@/components/charts";

const HOURS = Array.from({ length: 12 }, (_, i) => 8 + i); // 08:00 .. 19:00

export function startOfWeek(d: Date): Date {
  const x = new Date(d);
  const day = (x.getDay() + 6) % 7; // Monday = 0
  x.setDate(x.getDate() - day);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

export function ymd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function WeekCalendar({
  weekStart,
  appointments,
  dayLabels,
  onPick,
}: {
  weekStart: Date;
  appointments: ManagerAppointment[];
  dayLabels: string[];
  onPick?: (a: ManagerAppointment) => void;
}) {
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  const todayKey = ymd(new Date());

  const grid: Record<string, Record<number, ManagerAppointment[]>> = {};
  for (const a of appointments) {
    if (!a.scheduled_at) continue;
    const dkey = a.scheduled_at.slice(0, 10);
    const hour = parseInt(a.scheduled_at.slice(11, 13), 10);
    (grid[dkey] ??= {})[hour] ??= [];
    grid[dkey][hour].push(a);
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[860px]">
        <div className="grid" style={{ gridTemplateColumns: "56px repeat(7, 1fr)" }}>
          <div />
          {days.map((d, i) => {
            const isToday = ymd(d) === todayKey;
            return (
              <div
                key={i}
                className={`border-b border-slate-200 px-2 py-2 text-center text-xs font-medium ${isToday ? "bg-blue-50 text-blue-700" : "text-slate-600"}`}
              >
                <div>{dayLabels[i]}</div>
                <div className={isToday ? "text-blue-500" : "text-slate-400"}>
                  {String(d.getDate()).padStart(2, "0")}.{String(d.getMonth() + 1).padStart(2, "0")}
                </div>
              </div>
            );
          })}

          {HOURS.map((h) => (
            <React.Fragment key={h}>
              <div className="border-t border-slate-100 px-1 py-2 text-right text-[11px] text-slate-400">
                {String(h).padStart(2, "0")}:00
              </div>
              {days.map((d, i) => {
                const items = grid[ymd(d)]?.[h] ?? [];
                return (
                  <div key={i} className="min-h-[46px] border-l border-t border-slate-100 p-1">
                    {items.map((a) => (
                      <button
                        key={a.id}
                        onClick={() => onPick?.(a)}
                        className="mb-1 block w-full rounded border-l-4 bg-slate-50 px-1.5 py-1 text-left text-[11px] hover:bg-slate-100"
                        style={{ borderColor: color(statusColor(a.status)) }}
                      >
                        <div className="truncate font-medium text-slate-800">
                          {a.scheduled_at?.slice(11, 16)} {a.patient_short ?? ""}
                        </div>
                        <div className="truncate text-slate-500">{a.doctor_name ?? a.service}</div>
                      </button>
                    ))}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
