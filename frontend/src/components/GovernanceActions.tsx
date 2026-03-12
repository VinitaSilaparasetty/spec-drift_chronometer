import React, { useState } from 'react';

export default function GovernanceActions() {
  const [status, setStatus] = useState('READY');

  const triggerAudit = async () => {
    setStatus('AUDITING');
    try {
      await fetch('http://localhost:8000/audit', { method: 'POST' });
      setStatus('SUCCESS');
      setTimeout(() => setStatus('READY'), 3000);
    } catch (e) {
      setStatus('ERROR');
      setTimeout(() => setStatus('READY'), 3000);
    }
  };

  const downloadAudit = () => {
    window.open('http://localhost:8000/download-audit', '_blank');
  };

  return (
    <div className="flex gap-3 mt-6 p-4 bg-black/30 border border-slate-800 rounded-xl backdrop-blur-sm">
      <button
        onClick={triggerAudit}
        className={`flex-1 py-2 px-4 rounded-lg text-xs font-bold tracking-widest transition-all transform active:scale-95 ${
          status === 'AUDITING' 
          ? "bg-amber-500/20 text-amber-400 animate-pulse border border-amber-500/50" 
          : "bg-amber-600 hover:bg-amber-500 text-white shadow shadow-amber-900/40 uppercase"
        }`}
      >
        {status === 'AUDITING' ? "VERIFYING..." : "Run Audit"}
      </button>

      <button
        onClick={downloadAudit}
        className="flex-1 py-2 px-4 rounded-lg text-xs font-bold tracking-widest bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all uppercase"
      >
        Download Audit
      </button>
    </div>
  );
}
