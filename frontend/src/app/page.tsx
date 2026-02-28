'use client';

import React, { useState, useEffect } from 'react';

export default function DriftDashboard() {
  const [driftIndex, setDriftIndex] = useState<string>('0.0000');
  const [systemHealth, setSystemHealth] = useState<string>('CONNECTING');

  useEffect(() => {
    const fetchDrift = async () => {
      try {
        // Points to your FastAPI 'backend.main:app'
        const response = await fetch('http://localhost:8000/drift');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        // Assuming your backend returns { "drift": 0.0004 }
        setDriftIndex(data.drift.toFixed(4));
        setSystemHealth('SOVEREIGN');
      } catch (error) {
        console.error('Fetch error:', error);
        setSystemHealth('OFFLINE');
      }
    };

    const interval = setInterval(fetchDrift, 2000); // Poll every 2 seconds
    fetchDrift(); // Initial call
    
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { label: 'System Health', value: systemHealth, color: systemHealth === 'SOVEREIGN' ? 'text-emerald-400' : 'text-red-400' },
    { label: 'Drift Index', value: driftIndex, color: 'text-blue-400' },
    { label: 'Active Swarms', value: '12', color: 'text-white' },
    { label: 'Warden Status', value: 'Observing', color: 'text-amber-400' },
  ];

  return (
    <main className="min-h-screen bg-black text-zinc-100 p-8 font-sans selection:bg-emerald-500/30">
      <header className="max-w-7xl mx-auto mb-12 flex justify-between items-end border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-4xl font-light tracking-tighter uppercase italic">
            Spec-Drift <span className="font-bold not-italic">Chronometer</span>
          </h1>
          <p className="text-zinc-500 text-sm mt-2 font-mono uppercase tracking-widest">
            Aevoxis Governance Layer // 2026.02.25
          </p>
        </div>
        <div className="flex gap-4 text-xs font-mono">
          <span className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${systemHealth === 'SOVEREIGN' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            {systemHealth === 'SOVEREIGN' ? 'LIVE_FEED' : 'CONNECTION_LOST'}
          </span>
        </div>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-sm">
            <p className="text-zinc-500 text-xs uppercase tracking-wider mb-1">{stat.label}</p>
            <p className={`text-2xl font-mono ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <section className="lg:col-span-2 bg-zinc-900/30 border border-zinc-800 p-8 rounded-sm">
          <h2 className="text-sm font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
            <span className="w-1 h-4 bg-emerald-500" /> Drift Variance Analysis
          </h2>
          <div className="h-64 flex items-end gap-2 border-b border-zinc-800 pb-2">
            {[40, 70, 45, 90, 65, 80, 30, 95, 50].map((h, i) => (
              <div 
                key={i} 
                className="flex-1 bg-zinc-800 hover:bg-emerald-500/50 transition-colors cursor-crosshair" 
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
          <p className="mt-4 text-xs text-zinc-500 font-mono italic">
            * Real-time variance detected across 4 localized sub-swarms.
          </p>
        </section>

        <section className="bg-zinc-900/30 border border-zinc-800 p-8 rounded-sm">
          <h2 className="text-sm font-bold uppercase tracking-widest mb-6">Warden Logs</h2>
          <div className="space-y-4 font-mono text-[10px] leading-relaxed text-zinc-400">
            <p><span className="text-zinc-600">[19:45:01]</span> SEC_AUDIT_PASS: Swarm delta within limits.</p>
            <p><span className="text-zinc-600">[19:44:58]</span> ADJ_SYNC: Re-aligning temporal offset.</p>
            <p className="text-emerald-400"><span className="text-zinc-600">[19:44:52]</span> GENESIS_INTENT: Verified via Ledger.</p>
            <p><span className="text-zinc-600">[19:44:45]</span> SENSOR_SCAN: Latency at 4ms.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
