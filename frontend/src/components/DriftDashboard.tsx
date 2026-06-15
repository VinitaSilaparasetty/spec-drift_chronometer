"use client";
import React, { useState } from "react";
import GovernanceActions from "./GovernanceActions";
import JustificationGate from "./JustificationGate";
import GuidedTour from "./GuidedTour";

interface DriftPoint {
  time: string;
  drift: number;
  status: string;
}

interface Props {
  driftData: DriftPoint[];
  currentStatus: string;
  gateStatus: string;
  currentDrift: number;
  demoMode?: boolean;
}

const DRIFT_THRESHOLD = 0.0075;
const MAX_DRIFT_DISPLAY = 0.015;

function barColor(drift: number): string {
  if (drift >= 0.012) return "bg-red-500";
  if (drift >= DRIFT_THRESHOLD) return "bg-amber-500";
  return "bg-emerald-500";
}

function statusColor(status: string): string {
  if (status === "CRITICAL_DRIFT" || status === "GATE_PENDING") return "text-red-400";
  if (status === "MONITORING" || status === "RESOLVING") return "text-amber-400";
  if (status === "CONNECTING" || status === "OFFLINE") return "text-zinc-500";
  return "text-emerald-400";
}

function generateLogs(driftData: DriftPoint[], gateStatus: string, gateDecision: string | null) {
  const entries: { time: string; text: string; level: "critical" | "warning" | "success" | "normal" }[] = [];

  if (gateStatus === "TRIGGERED") {
    entries.push({ time: "NOW", text: "ALERT: Drift threshold breached. Justification Gate ACTIVATED.", level: "critical" });
  } else if (gateStatus === "PENDING") {
    entries.push({ time: "NOW", text: "PENDING: Warden analyzing justification via Nova Pro...", level: "warning" });
  } else if (gateStatus === "RESOLVED" && gateDecision) {
    const level = gateDecision === "APPROVED" ? "success" : "critical";
    entries.push({ time: "NOW", text: `GATE RESOLVED: ${gateDecision}. Drift event logged to audit trail.`, level });
  }

  const recent = [...driftData].reverse().slice(0, 4);
  for (const pt of recent) {
    if (pt.status === "CRITICAL_DRIFT") {
      entries.push({ time: pt.time, text: `WARDEN: Drift ${pt.drift.toFixed(4)} exceeds sovereign threshold ${DRIFT_THRESHOLD}.`, level: "critical" });
    } else if (pt.status === "MONITORING" || pt.status === "RESOLVING") {
      entries.push({ time: pt.time, text: `MONITOR: Drift rising to ${pt.drift.toFixed(4)}. Warden sensors active.`, level: "warning" });
    } else if (pt.status === "SOVEREIGN") {
      entries.push({ time: pt.time, text: `SEC_AUDIT_PASS: Drift ${pt.drift.toFixed(4)} within sovereign limits.`, level: "normal" });
    }
  }

  if (entries.length === 0) {
    entries.push({ time: "--:--:--", text: "Awaiting first telemetry from Warden Engine...", level: "normal" });
  }

  return entries.slice(0, 6);
}

export default function DriftDashboard({ driftData, currentStatus, gateStatus, currentDrift, demoMode }: Props) {
  const [gateDecision, setGateDecision] = useState<string | null>(null);
  const [showGate, setShowGate] = useState(false);

  const isLive = currentStatus !== "CONNECTING" && currentStatus !== "OFFLINE";
  const specCompliance = currentStatus === "CONNECTING" || currentStatus === "OFFLINE" ? "—" : currentStatus === "SOVEREIGN" || currentStatus === "RESOLVING" ? "100%" : currentStatus === "MONITORING" ? "94%" : "BREACH";
  const logs = generateLogs(driftData, gateStatus, gateDecision);

  // Show gate automatically when triggered
  React.useEffect(() => {
    if (gateStatus === "TRIGGERED" || gateStatus === "PENDING") {
      setShowGate(true);
    }
  }, [gateStatus]);

  const handleGateResolved = (decision: string) => {
    setGateDecision(decision);
  };

  return (
    <main className="min-h-screen bg-black text-zinc-100 p-6 font-sans selection:bg-emerald-500/30">

      {/* Header */}
      <header className="max-w-7xl mx-auto mb-10 flex flex-wrap justify-between items-end border-b border-zinc-800 pb-6 gap-4">
        <div>
          <h1 className="text-4xl font-light tracking-tighter uppercase italic">
            Spec-Drift <span className="font-bold not-italic">Chronometer</span>
          </h1>
          <p className="text-zinc-500 text-xs mt-2 font-mono uppercase tracking-widest">
            Aevoxis Governance Layer // EU AI Act Art. 12 &amp; 14 Compliant
            {demoMode && <span className="ml-3 text-amber-400 border border-amber-700 px-2 py-0.5 rounded text-[10px]">DEMO MODE</span>}
          </p>
        </div>
        <div className="flex gap-4 text-xs font-mono items-center">
          <span className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${isLive ? "bg-emerald-500 animate-pulse" : "bg-zinc-600"}`} />
            {isLive ? "LIVE_FEED" : "CONNECTING"}
          </span>
          {(gateStatus === "TRIGGERED" || gateStatus === "PENDING") && (
            <button
              onClick={() => setShowGate(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-red-900/40 border border-red-700 rounded text-red-400 animate-pulse hover:bg-red-900/60 transition-colors"
            >
              <span className="h-2 w-2 rounded-full bg-red-500" />
              JUSTIFICATION GATE ACTIVE
            </button>
          )}
        </div>
      </header>

      {/* Stat Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "System Health", value: currentStatus || "CONNECTING", color: statusColor(currentStatus), id: "" },
          { label: "Drift Index", value: currentDrift > 0 ? currentDrift.toFixed(4) : "0.0000", color: currentDrift > DRIFT_THRESHOLD ? "text-red-400" : "text-blue-400", id: "tour-drift-index" },
          { label: "Spec Compliance", value: specCompliance, color: specCompliance === "100%" ? "text-emerald-400" : specCompliance === "BREACH" ? "text-red-400" : "text-amber-400", id: "" },
          { label: "Warden Status", value: gateStatus === "CLEAR" || gateStatus === "RESOLVED" ? "Observing" : gateStatus === "TRIGGERED" ? "GATE OPEN" : "Analyzing", color: gateStatus === "TRIGGERED" ? "text-red-400" : gateStatus === "PENDING" ? "text-amber-400" : "text-amber-300", id: "" },
        ].map((s) => (
          <div key={s.label} id={s.id || undefined} className="bg-zinc-900/50 border border-zinc-800 p-5 rounded-sm">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">{s.label}</p>
            <p className={`text-xl font-mono font-bold ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Main content grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Drift Chart */}
        <section id="tour-drift-chart" className="lg:col-span-2 bg-zinc-900/30 border border-zinc-800 p-6 rounded-sm">
          <h2 className="text-xs font-bold uppercase tracking-widest mb-5 flex items-center gap-2">
            <span className="w-1 h-4 bg-emerald-500" /> Drift Variance Analysis
          </h2>

          {/* Threshold line label */}
          <div className="relative">
            <div
              className="absolute right-0 text-[9px] font-mono text-amber-500/70"
              style={{ bottom: `${(DRIFT_THRESHOLD / MAX_DRIFT_DISPLAY) * 100}%` }}
            >
              threshold
            </div>
            {/* Threshold dashed line */}
            <div
              className="absolute left-0 right-0 border-t border-dashed border-amber-700/40 pointer-events-none"
              style={{ bottom: `${(DRIFT_THRESHOLD / MAX_DRIFT_DISPLAY) * 100}%` }}
            />

            <div className="h-52 flex items-end gap-1 border-b border-zinc-800 pb-1">
              {driftData.length === 0
                ? [8,12,7,10,14,9,11,6,13,8,10,15,7,12,9,11,8,13,6,10].map((h, i) => (
                    <div key={i} className="flex-1 bg-zinc-800/40 rounded-t-sm" style={{ height: `${h}%` }} />
                  ))
                : driftData.map((pt, i) => (
                    <div
                      key={i}
                      title={`${pt.time}: ${pt.drift.toFixed(4)}`}
                      className={`flex-1 rounded-t-sm transition-all duration-500 cursor-crosshair ${barColor(pt.drift)}`}
                      style={{ height: `${Math.min((pt.drift / MAX_DRIFT_DISPLAY) * 100, 100)}%`, opacity: 0.7 + (i / driftData.length) * 0.3 }}
                    />
                  ))}
            </div>
          </div>

          <p className="mt-3 text-[10px] text-zinc-500 font-mono italic">
            Real-time semantic drift across governed sub-swarms. Threshold: {DRIFT_THRESHOLD}
          </p>

          {/* Governance Actions */}
          <div id="tour-governance"><GovernanceActions /></div>
        </section>

        {/* Right panel */}
        <div className="flex flex-col gap-6">

          {/* Warden Logs */}
          <section id="tour-warden-log" className="bg-zinc-900/30 border border-zinc-800 p-6 rounded-sm flex-1">
            <h2 className="text-xs font-bold uppercase tracking-widest mb-4">Warden Activity Log</h2>
            <div className="space-y-3 font-mono text-[10px] leading-relaxed">
              {logs.map((log, i) => (
                <p key={i} className={
                  log.level === "critical" ? "text-red-400" :
                  log.level === "warning" ? "text-amber-400" :
                  log.level === "success" ? "text-emerald-400" :
                  "text-zinc-400"
                }>
                  <span className="text-zinc-600">[{log.time}]</span>{" "}{log.text}
                </p>
              ))}
            </div>
          </section>

          {/* Spec Vault Summary */}
          <section id="tour-spec-vault" className="bg-zinc-900/30 border border-zinc-800 p-6 rounded-sm">
            <h2 className="text-xs font-bold uppercase tracking-widest mb-4">Sovereign Spec Vault</h2>
            <div className="space-y-2 font-mono text-[10px]">
              {[
                { file: "governance.md", status: "ACTIVE" },
                { file: "tech.md", status: "ACTIVE" },
                { file: "product.md", status: "ACTIVE" },
                { file: "human-intent-specs.md", status: "ACTIVE" },
                { file: "spec.json", status: "LOCKED" },
              ].map((s) => (
                <div key={s.file} className="flex justify-between items-center">
                  <span className="text-zinc-500">.kiro/steering/{s.file}</span>
                  <span className={s.status === "LOCKED" ? "text-red-400" : "text-emerald-400"}>
                    {s.status}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>

      <GuidedTour />

      {/* Justification Gate Modal */}
      {showGate && (
        <JustificationGate
          driftValue={currentDrift}
          gateStatus={gateStatus}
          onResolved={(decision) => {
            handleGateResolved(decision);
            if (gateStatus === "RESOLVED") setShowGate(false);
          }}
          onDismiss={() => setShowGate(false)}
        />
      )}
    </main>
  );
}
