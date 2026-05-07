import { AlertTriangle } from "lucide-react";
import type { Anomaly } from "@/types";

const SEVERITY_STYLE = (s: number) => {
  if (s >= 8) return "bg-red-950/60 text-[#EF2B2D] border-red-700/50";
  if (s >= 6) return "bg-orange-950/60 text-orange-400 border-orange-700/50";
  if (s >= 4) return "bg-amber-950/60 text-amber-400 border-amber-700/50";
  return "bg-[#132238] text-[#64748B] border-[#1E3A5F]";
};

interface Props { anomalies: Anomaly[] }

export function AnomalyList({ anomalies }: Props) {
  if (anomalies.length === 0) {
    return (
      <div className="card px-5 py-8 text-center text-[#64748B] text-sm font-mono">
        Anormallik tespit edilmedi.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {anomalies.map((a, i) => (
        <div key={i} className="card card-hover p-4 flex items-start gap-4">
          <div
            className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg border text-xs font-bold font-mono ${SEVERITY_STYLE(a.severity)}`}
          >
            {a.severity}/10
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle
                size={13}
                className={a.severity >= 8 ? "text-[#EF2B2D]" : "text-amber-400"}
              />
              <span className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest font-mono">
                {a.type}
              </span>
            </div>
            <p className="text-sm text-[#E2E8F0] leading-snug">{a.description}</p>
            {a.affected_entity && (
              <p className="mt-1 text-xs text-[#64748B]">
                Varlık:{" "}
                <span className="font-mono text-[#00D4FF]">{a.affected_entity}</span>
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}