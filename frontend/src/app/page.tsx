"use client";
import React, { useState, useEffect } from "react";
import DriftDashboard from "@/components/DriftDashboard";

interface DriftPoint {
  time: string;
  drift: number;
  status: string;
}

export default function Page() {
  const [driftData, setDriftData] = useState<DriftPoint[]>([]);
  const [currentStatus, setCurrentStatus] = useState("CONNECTING");
  const [gateStatus, setGateStatus] = useState("CLEAR");
  const [currentDrift, setCurrentDrift] = useState(0);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

    const fetchDrift = async () => {
      try {
        const res = await fetch(`${apiUrl}/drift`);
        if (!res.ok) throw new Error("Non-OK");
        const data = await res.json();

        setCurrentDrift(data.drift ?? 0);
        setCurrentStatus(data.status ?? "SOVEREIGN");
        setGateStatus(data.gate ?? "CLEAR");
        setDemoMode(!!data.demo_mode);

        setDriftData((prev) => [
          ...prev.slice(-19),
          { time: new Date().toLocaleTimeString(), drift: data.drift ?? 0, status: data.status ?? "SOVEREIGN" },
        ]);
      } catch {
        setCurrentStatus("OFFLINE");
      }
    };

    fetchDrift();
    const interval = setInterval(fetchDrift, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DriftDashboard
      driftData={driftData}
      currentStatus={currentStatus}
      gateStatus={gateStatus}
      currentDrift={currentDrift}
      demoMode={demoMode}
    />
  );
}
