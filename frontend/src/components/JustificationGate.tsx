"use client";
import React, { useState } from "react";

interface Props {
  driftValue: number;
  gateStatus: string;
  onResolved: (decision: string) => void;
  onDismiss: () => void;
}

export default function JustificationGate({ driftValue, gateStatus, onResolved, onDismiss }: Props) {
  const [justification, setJustification] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ decision: string; reasoning_trace: string; model: string; verification_hash: string } | null>(null);
  const [error, setError] = useState("");

  const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

  const handleSubmit = async () => {
    if (!justification.trim()) {
      setError("A justification is required before the Warden will analyze the drift.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/gate/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ justification, drift_value: driftValue }),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
        onResolved(data.decision);
      }
    } catch {
      setError("Could not reach the Warden Engine. Ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const isResolved = result !== null;
  const approved = result?.decision === "APPROVED";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-zinc-950 border border-red-900/60 rounded-sm shadow-2xl shadow-red-950/40">

        {/* Header */}
        <div className={`px-6 py-4 border-b flex items-center justify-between ${isResolved ? (approved ? "border-emerald-900/60 bg-emerald-950/30" : "border-red-900/60 bg-red-950/30") : "border-red-900/40 bg-red-950/20"}`}>
          <div className="flex items-center gap-3">
            <span className={`h-3 w-3 rounded-full ${isResolved ? (approved ? "bg-emerald-500" : "bg-red-500") : "bg-red-500 animate-pulse"}`} />
            <div>
              <p className="text-xs font-mono font-bold uppercase tracking-widest text-red-300">
                {isResolved ? `Justification Gate — ${result?.decision}` : "Justification Gate — ACTIVE"}
              </p>
              <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
                EU AI Act Article 14 · Human-in-the-Loop Required
              </p>
            </div>
          </div>
          {isResolved && (
            <button onClick={onDismiss} className="text-zinc-500 hover:text-zinc-300 text-xs font-mono uppercase tracking-wider">
              Close ×
            </button>
          )}
        </div>

        <div className="p-6 space-y-5">

          {/* Drift alert */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-4 font-mono text-xs">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-zinc-400 uppercase tracking-wider text-[10px] mb-1">Drift Detected</p>
                <p className="text-red-400 text-2xl font-bold">{driftValue.toFixed(4)}</p>
              </div>
              <div className="text-right">
                <p className="text-zinc-400 uppercase tracking-wider text-[10px] mb-1">Sovereign Threshold</p>
                <p className="text-zinc-300 text-2xl font-bold">0.0075</p>
              </div>
              <div className="text-right">
                <p className="text-zinc-400 uppercase tracking-wider text-[10px] mb-1">Excess Delta</p>
                <p className="text-amber-400 text-2xl font-bold">{(driftValue - 0.0075) > 0 ? "+" : ""}{(driftValue - 0.0075).toFixed(4)}</p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-zinc-800 text-zinc-500 text-[10px]">
              Spec reference: <span className="text-zinc-300">.kiro/steering/tech.md §2</span> · Model: <span className="text-zinc-300">amazon.nova-pro-v1:0</span>
            </div>
          </div>

          {!isResolved ? (
            <>
              <div>
                <p className="text-[10px] font-mono text-zinc-500 bg-zinc-900/60 border border-zinc-800 rounded-sm px-3 py-2 mb-3 leading-relaxed">
                  <span className="text-zinc-400 font-bold">Data notice:</span> Your justification text will be logged in the compliance audit trail under EU AI Act Article 12 and retained for 90 days. Do not include sensitive personal data. Records can be erased on request under GDPR Article 17.
                </p>
                <label className="block text-[10px] font-mono uppercase tracking-widest text-zinc-400 mb-2">
                  Sovereign Justification — Required for Article 14 Compliance
                </label>
                <textarea
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-sm p-3 text-xs font-mono text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-amber-700 resize-none h-28"
                  placeholder="Explain why this architectural drift is intentional and justified. E.g., 'Migrating auth layer to OAuth2 to satisfy new compliance requirements from legal. This deviates from the DynamoDB session schema but is required for GDPR Article 7 compliance...'"
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  disabled={loading}
                />
                {error && <p className="text-red-400 text-[10px] font-mono mt-1">{error}</p>}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 py-2.5 px-4 bg-amber-700 hover:bg-amber-600 disabled:bg-zinc-700 disabled:cursor-wait text-white text-xs font-bold tracking-widest uppercase rounded-sm transition-colors"
                >
                  {loading ? "Warden Analyzing..." : "Submit to Warden Agent"}
                </button>
              </div>

              {loading && (
                <div className="flex items-center gap-2 text-[10px] font-mono text-amber-400 animate-pulse">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  Invoking amazon.nova-pro-v1:0 in eu-central-1 for reasoning analysis...
                </div>
              )}
            </>
          ) : (
            <>
              {/* Decision badge */}
              <div className={`flex items-center gap-3 p-3 rounded-sm border ${approved ? "bg-emerald-950/40 border-emerald-800/50" : "bg-red-950/40 border-red-800/50"}`}>
                <span className={`text-2xl font-bold font-mono ${approved ? "text-emerald-400" : "text-red-400"}`}>
                  {result?.decision}
                </span>
                <div className="text-[10px] font-mono text-zinc-400">
                  <p>Model: <span className="text-zinc-200">{result?.model}</span></p>
                  <p>Hash: <span className="text-zinc-200">{result?.verification_hash}</span></p>
                </div>
              </div>

              {/* Reasoning trace */}
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-400 mb-2">Warden Reasoning Trace</p>
                <pre className="bg-zinc-900 border border-zinc-800 rounded-sm p-3 text-[10px] font-mono text-zinc-300 overflow-auto max-h-52 whitespace-pre-wrap leading-relaxed">
                  {result?.reasoning_trace}
                </pre>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={onDismiss}
                  className="flex-1 py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-bold tracking-widest uppercase rounded-sm transition-colors"
                >
                  Close Gate — Return to Dashboard
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
