import React, { useState } from "react";

export default function GovernanceActions() {
  const [status, setStatus] = useState("READY");
  const [message, setMessage] = useState("");

  const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

  const triggerAudit = async () => {
    setStatus("AUDITING");
    setMessage("");
    try {
      const response = await fetch(`${apiUrl}/audit`, { method: "POST" });
      if (response.ok) {
        setStatus("SUCCESS");
        setMessage("AUDIT TRAIL GENERATED");
        setTimeout(() => { setStatus("READY"); setMessage(""); }, 4000);
      } else {
        throw new Error("Non-OK response");
      }
    } catch {
      setStatus("ERROR");
      setMessage("CONNECTION FAILED — IS BACKEND RUNNING?");
      setTimeout(() => { setStatus("READY"); setMessage(""); }, 4000);
    }
  };

  const downloadAudit = () => {
    window.open(`${apiUrl}/download-audit`, "_blank");
  };

  return (
    <div className="mt-5">
      <div className="flex gap-3 p-4 bg-black/40 border border-zinc-800 rounded-sm">
        <button
          onClick={triggerAudit}
          disabled={status === "AUDITING"}
          className={`flex-1 py-2 px-4 rounded-sm text-xs font-bold tracking-widest transition-all uppercase ${
            status === "AUDITING"
              ? "bg-amber-500/20 text-amber-400 animate-pulse border border-amber-700/50 cursor-wait"
              : status === "SUCCESS"
              ? "bg-emerald-700 text-white"
              : "bg-amber-700 hover:bg-amber-600 text-white"
          }`}
        >
          {status === "AUDITING" ? "Generating..." : status === "SUCCESS" ? "Done" : "Run Audit"}
        </button>

        <button
          onClick={downloadAudit}
          className="flex-1 py-2 px-4 rounded-sm text-xs font-bold tracking-widest bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 transition-all uppercase"
        >
          Download Audit
        </button>
      </div>

      {message && (
        <p className={`mt-2 text-center text-[10px] font-mono font-bold tracking-widest ${
          status === "ERROR" ? "text-red-500" : "text-emerald-400"
        }`}>
          {message}
        </p>
      )}
    </div>
  );
}
