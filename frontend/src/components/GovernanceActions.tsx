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
        className={`flex-1 py-2.5 px-5 rounded-lg text-sm font-semibold transition-all transform active:scale-95 ${
          status === 'AUDITING' 
          ? "bg-amber-500/30 text-amber-200 animate-pulse" 
          : "bg-amber-600 hover:bg-amber-500 text-white shadow shadow-amber-900/40"
        }`}
      >
        {status === 'AUDITING' ? "VERIFYING INTEGRITY..." : "RUN SOVEREIGN AUDIT"}
      </button>

      <button
        onClick={downloadAudit}
        className="flex-1 py-2.5 px-5 rounded-lg text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all"
      >
        DOWNLOAD AUDIT TRAIL
      </button>
    </div>
  );
}
