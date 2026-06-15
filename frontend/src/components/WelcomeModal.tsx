"use client";
import React, { useEffect, useState } from "react";

const SESSION_KEY = "sdc_welcome_dismissed";

export default function WelcomeModal() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!sessionStorage.getItem(SESSION_KEY)) {
      setVisible(true);
    }
  }, []);

  const dismiss = () => {
    sessionStorage.setItem(SESSION_KEY, "1");
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-zinc-950 border border-zinc-800 rounded-sm shadow-2xl">

        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse" />
            <div>
              <p className="text-xs font-mono font-bold uppercase tracking-widest text-emerald-400">
                Welcome to the Spec-Drift Chronometer
              </p>
              <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
                Aevoxis Warden Engine · EU AI Act Article 14 Demo
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-3">
          <p className="text-xs text-zinc-400 font-mono leading-relaxed">
            This demo shows a real-time AI governance system enforcing EU AI Act Article 14 human oversight. Here is what will happen:
          </p>

          <ol className="space-y-2.5 font-mono text-[11px]">
            {[
              { n: "01", color: "text-zinc-400", text: "Watch the Drift Index on the dashboard rise over the next 45 seconds." },
              { n: "02", color: "text-amber-400", text: "When it crosses the sovereign threshold a Justification Gate will appear automatically." },
              { n: "03", color: "text-zinc-300", text: <>In the gate, type something like: <span className="text-emerald-400 italic">"Migrating auth layer to OAuth2 for GDPR Article 7 compliance, approved by legal team on today's date."</span></> },
              { n: "04", color: "text-zinc-400", text: "Click Submit to Warden Agent." },
              { n: "05", color: "text-emerald-400", text: "The Warden will evaluate your justification and return APPROVED or REJECTED with a full reasoning trace." },
              { n: "06", color: "text-zinc-400", text: "Click Download Audit to export your compliance record." },
            ].map(({ n, color, text }) => (
              <li key={n} className="flex items-start gap-3">
                <span className="text-zinc-600 shrink-0">[{n}]</span>
                <span className={color}>{text}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Footer */}
        <div className="px-6 pb-5">
          <button
            onClick={dismiss}
            className="w-full py-2.5 px-4 bg-amber-700 hover:bg-amber-600 text-white text-xs font-bold tracking-widest uppercase rounded-sm transition-colors"
          >
            Start Demo
          </button>
        </div>

      </div>
    </div>
  );
}
