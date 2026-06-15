"use client";
import { useEffect } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";

const SESSION_KEY = "sdc_tour_dismissed";

export default function GuidedTour() {
  useEffect(() => {
    if (sessionStorage.getItem(SESSION_KEY)) return;

    const driverObj = driver({
      animate: true,
      smoothScroll: true,
      allowClose: true,
      overlayOpacity: 0.75,
      stagePadding: 6,
      stageRadius: 2,
      popoverClass: "sdc-popover",
      onDestroyed: () => sessionStorage.setItem(SESSION_KEY, "1"),
      steps: [
        {
          element: "#tour-drift-index",
          popover: {
            title: "Watch this number",
            description:
              "This is the live Drift Index. It rises every 3 seconds. When it crosses <strong>0.0075</strong> the Justification Gate triggers automatically — give it about <strong>45 seconds</strong>.",
            side: "bottom",
            align: "start",
          },
        },
        {
          element: "#tour-drift-chart",
          popover: {
            title: "Live drift readings",
            description:
              "Each bar is one reading. <strong style='color:#10b981'>Green</strong> = within sovereign limits. <strong style='color:#f59e0b'>Amber</strong> = drift rising. <strong style='color:#ef4444'>Red</strong> = threshold crossed, gate active.",
            side: "top",
            align: "start",
          },
        },
        {
          element: "#tour-warden-log",
          popover: {
            title: "Warden Activity Log",
            description:
              "Every governance event is logged here the moment it happens. Watch this update as drift rises and again when the gate resolves.",
            side: "left",
            align: "start",
          },
        },
        {
          element: "#tour-spec-vault",
          popover: {
            title: "Sovereign Spec Vault",
            description:
              "These are your human-authored architectural intent files. The Warden cross-references every justification against these before issuing a decision.",
            side: "left",
            align: "start",
          },
        },
        {
          element: "#tour-governance",
          popover: {
            title: "Audit controls",
            description:
              "After the Justification Gate resolves, click <strong>Run Audit</strong> then <strong>Download Audit</strong> to export your Article 12 compliance record.",
            side: "top",
            align: "start",
          },
        },
      ],
    });

    // Short delay so the dashboard renders before the tour starts
    const t = setTimeout(() => driverObj.drive(), 600);
    return () => clearTimeout(t);
  }, []);

  return null;
}
