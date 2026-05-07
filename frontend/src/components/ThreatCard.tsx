"use client";

import { ChevronDown, ChevronUp, Shield, Terminal } from "lucide-react";
import { useState } from "react";
import type { IdentifiedThreat } from "@/types";

interface Props {
  threat: IdentifiedThreat;
  index: number;
}

export function ThreatCard({ threat, index }: Props) {
  const [open, setOpen] = useState(index === 0);

  return (
    <div className="card overflow-hidden card-hover">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-4 p-5 text-left hover:bg-[#132238] transition-colors"
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#EF2B2D]/10 border border-[#EF2B2D]/30 text-[#EF2B2D] flex items-center justify-center text-sm font-bold font-mono">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <span className="inline-block text-xs font-bold bg-[#EF2B2D] text-white px-2.5 py-0.5 rounded mb-1.5 uppercase tracking-wide">
            {threat.threat_type}
          </span>
          <p className="text-sm font-semibold text-[#E2E8F0] leading-snug">{threat.description}</p>
        </div>
        {open
          ? <ChevronUp size={18} className="text-[#64748B] flex-shrink-0 mt-0.5" />
          : <ChevronDown size={18} className="text-[#64748B] flex-shrink-0 mt-0.5" />}
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-[#1E3A5F] pt-4 space-y-4">
          <Field icon={<Shield size={14} />} label="Kanıt" value={threat.evidence} />
          <div>
            <p className="text-xs font-semibold text-[#00D4FF] uppercase tracking-widest mb-2">
              Etkilenen Varlıklar
            </p>
            <div className="flex flex-wrap gap-2">
              {threat.affected_assets.map((a) => (
                <span
                  key={a}
                  className="font-mono text-xs bg-[#132238] text-[#E2E8F0] px-2.5 py-1 rounded-md border border-[#1E3A5F]"
                >
                  {a}
                </span>
              ))}
            </div>
          </div>
          <div className="bg-emerald-950/50 border-l-4 border-emerald-500 rounded-r-lg px-4 py-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Terminal size={13} className="text-emerald-400" />
              <p className="text-xs font-bold text-emerald-400 uppercase tracking-widest">
                Önerilen Eylem
              </p>
            </div>
            <p className="text-sm text-emerald-200">{threat.recommended_action}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-[#64748B]">{icon}</span>
        <p className="text-xs font-semibold text-[#64748B] uppercase tracking-widest">{label}</p>
      </div>
      <p className="text-sm text-[#E2E8F0] leading-relaxed">{value}</p>
    </div>
  );
}