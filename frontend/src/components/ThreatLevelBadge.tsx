import type { ThreatLevel } from "@/types";

const STYLES: Record<ThreatLevel, string> = {
  low:      "bg-emerald-950/60 text-emerald-400 border-emerald-700/50",
  medium:   "bg-amber-950/60   text-amber-400   border-amber-700/50",
  high:     "bg-orange-950/60  text-orange-400  border-orange-700/50",
  critical: "bg-red-950/60     text-[#EF2B2D]   border-red-700/50",
};

const LABELS_TR: Record<ThreatLevel, string> = {
  low:      "Düşük",
  medium:   "Orta",
  high:     "Yüksek",
  critical: "Kritik",
};

interface Props {
  level: ThreatLevel;
  size?: "sm" | "md" | "lg";
}

export function ThreatLevelBadge({ level, size = "md" }: Props) {
  const sizeClass =
    size === "sm"
      ? "text-xs px-2 py-0.5"
      : size === "lg"
      ? "text-base px-4 py-1.5 font-bold"
      : "text-sm px-3 py-1";
  return (
    <span
      className={`inline-flex items-center rounded-full border font-semibold uppercase tracking-widest font-mono ${sizeClass} ${STYLES[level]}`}
    >
      {LABELS_TR[level]}
    </span>
  );
}