"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft, Download, Loader2, AlertTriangle, CheckCircle2,
  Clock, XCircle, Shield, BarChart3, Database, List
} from "lucide-react";
import { api } from "@/lib/api";
import { ThreatLevelBadge } from "@/components/ThreatLevelBadge";
import { ThreatCard } from "@/components/ThreatCard";
import { StatsTable } from "@/components/StatsTable";
import { AnomalyList } from "@/components/AnomalyList";
import type { AnalysisRead, HeuristicReport, ThreatReport } from "@/types";

// ─── Durum mesajları ─────────────────────────────────────────────────────────

const STATUS_MESSAGES: Record<string, { icon: React.ReactNode; label: string; sub: string }> = {
  pending: {
    icon: <Clock size={36} className="text-[#64748B]" />,
    label: "Analize alındı",
    sub: "Log dosyanız kuyruğa alındı. Analiz kısa süre içinde başlayacak.",
  },
  processing: {
    icon: <Loader2 size={36} className="text-[#00D4FF] animate-spin" />,
    label: "Analiz sürüyor",
    sub: "Olaylar ayrıştırılıyor, desenler tespit ediliyor ve yapay zeka analisti devreye giriyor.",
  },
  failed: {
    icon: <XCircle size={36} className="text-[#EF2B2D]" />,
    label: "Analiz başarısız",
    sub: "İşlem sırasında bir hata oluştu.",
  },
};

// progress_step: 1=dosya, 2=ayrıştırma, 3=buluşsal, 4=LLM, 5=bitti
const PROCESSING_STEPS: { label: string; step: number }[] = [
  { label: "Dosya hazırlanıyor",                  step: 1 },
  { label: "Log olayları ayrıştırılıyor",         step: 2 },
  { label: "Buluşsal analiz çalıştırılıyor",      step: 3 },
  { label: "Yapay zeka analisti devreye giriyor", step: 4 },
];

type Tab = "summary" | "threats" | "statistics" | "raw";

// ─── Ana sayfa ────────────────────────────────────────────────────────────────

export default function AnalysisDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const analysisId = parseInt(id, 10);
  const [tab, setTab] = useState<Tab>("summary");

  const { data: analysis, error } = useQuery<AnalysisRead>({
    queryKey: ["analysis", analysisId],
    queryFn: () => api.getAnalysis(analysisId).then((r) => r.data),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 2500 : false;
    },
  });

  const isComplete = analysis?.status === "completed";

  return (
    <div className="min-h-screen bg-[#060D17]">
      {/* NAV */}
      <nav className="nav-dark">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-[#64748B] hover:text-[#E2E8F0] text-sm font-medium transition-colors"
            >
              <ArrowLeft size={16} /> Kontrol Paneli
            </Link>
            <span className="text-[#1E3A5F]">|</span>
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded overflow-hidden flex-shrink-0">
                <Image src="/cassandra-logo.png" alt="Cassandra" width={28} height={28} className="w-full h-full object-cover" />
              </div>
              <span className="font-bold text-[#E2E8F0] text-sm font-mono">
                Analiz #{analysisId}
              </span>
            </div>
          </div>
          {isComplete && (
            <a href={api.getPdfUrl(analysisId)} download className="btn-primary text-sm">
              <Download size={15} /> PDF İndir
            </a>
          )}
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Yükleniyor */}
        {!analysis && !error && (
          <div className="flex items-center justify-center py-24 gap-3 text-[#64748B]">
            <Loader2 size={22} className="animate-spin text-[#00D4FF]" />
            <span className="text-sm font-mono">Analiz yükleniyor…</span>
          </div>
        )}

        {/* Hata */}
        {error && (
          <div className="card px-6 py-5 border-[#EF2B2D]/30 bg-[#EF2B2D]/5 flex items-center gap-3">
            <AlertTriangle size={18} className="text-[#EF2B2D]" />
            <p className="text-sm text-[#EF2B2D]">Analiz yüklenemedi. Lütfen sayfayı yenileyin.</p>
          </div>
        )}

        {/* İşleniyor / Başarısız durumu */}
        {analysis && !isComplete && (
          <div className="card max-w-lg mx-auto mt-8 p-10 text-center">
            <div className="flex justify-center mb-6">
              {STATUS_MESSAGES[analysis.status]?.icon}
            </div>
            <h2 className="text-lg font-bold text-[#E2E8F0] mb-2">
              {STATUS_MESSAGES[analysis.status]?.label}
            </h2>
            <p className="text-sm text-[#64748B] mb-6">
              {analysis.status === "failed" && analysis.error_message
                ? analysis.error_message
                : STATUS_MESSAGES[analysis.status]?.sub}
            </p>
            {analysis.status === "failed" && (
              <Link href="/upload" className="btn-primary text-sm">
                Tekrar Dene
              </Link>
            )}
            {(analysis.status === "pending" || analysis.status === "processing") && (
              <div className="space-y-2">
                {PROCESSING_STEPS.map(({ label, step }) => {
                  const current = analysis.progress_step ?? 0;
                  const done    = current > step;
                  const active  = current === step;
                  return (
                    <div
                      key={step}
                      className={`flex items-center gap-3 text-sm px-4 py-2 rounded-lg transition-colors font-mono ${
                        active
                          ? "bg-[#00D4FF]/10 text-[#00D4FF] font-medium border border-[#00D4FF]/20"
                          : done
                          ? "text-emerald-400"
                          : "text-[#64748B]"
                      }`}
                    >
                      {done
                        ? <CheckCircle2 size={14} className="text-emerald-400" />
                        : active
                        ? <Loader2 size={14} className="animate-spin" />
                        : <div className="w-3.5 h-3.5 rounded-full border-2 border-[#1E3A5F]" />}
                      {label}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Kısmi tamamlanma: buluşsal rapor var ama LLM geçici hata aldı */}
        {analysis && isComplete && analysis.heuristic_report && !analysis.threat_report && (
          <div className="space-y-4">
            <div className="card px-6 py-4 border-amber-800/40 bg-amber-950/20 flex items-center gap-3">
              <AlertTriangle size={18} className="text-amber-400 flex-shrink-0" />
              <p className="text-sm text-amber-200">
                Yapay zeka analisti geçici olarak kullanılamıyor — istatistiksel analiz tamamlandı. Tehdit raporu için lütfen birkaç dakika sonra tekrar deneyin.
              </p>
            </div>
            <CompletedView
              analysis={analysis}
              threat={null}
              heuristic={analysis.heuristic_report}
              tab={tab}
              setTab={setTab}
              analysisId={analysisId}
            />
          </div>
        )}

        {/* Tam tamamlanma */}
        {analysis && isComplete && analysis.threat_report && analysis.heuristic_report && (
          <CompletedView
            analysis={analysis}
            threat={analysis.threat_report}
            heuristic={analysis.heuristic_report}
            tab={tab}
            setTab={setTab}
            analysisId={analysisId}
          />
        )}
      </main>
    </div>
  );
}

// ─── Tamamlandı görünümü ─────────────────────────────────────────────────────

function CompletedView({
  analysis, threat, heuristic, tab, setTab, analysisId,
}: {
  analysis: AnalysisRead;
  threat: ThreatReport | null;
  heuristic: HeuristicReport;
  tab: Tab;
  setTab: (t: Tab) => void;
  analysisId: number;
}) {
  const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "summary",    label: "Özet",                                               icon: <Shield size={15} /> },
    { id: "threats",    label: `Tehditler (${threat?.identified_threats.length ?? 0})`, icon: <AlertTriangle size={15} /> },
    { id: "statistics", label: "İstatistikler",                                      icon: <BarChart3 size={15} /> },
    { id: "raw",        label: "Ham Veri",                                           icon: <Database size={15} /> },
  ];

  return (
    <div className="space-y-6">
      {/* Başlık kartı */}
      <div className="card p-6 flex flex-wrap items-start gap-6 card-hover">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            {threat && <ThreatLevelBadge level={threat.threat_level} size="lg" />}
            {threat && (
              <span className="text-sm text-[#64748B] font-mono">
                Güven:{" "}
                <strong className="text-[#E2E8F0]">{threat.confidence_score}%</strong>
              </span>
            )}
            <span className="text-sm text-[#64748B] font-mono">
              Olay:{" "}
              <strong className="text-[#E2E8F0]">{heuristic.total_events.toLocaleString("tr-TR")}</strong>
            </span>
            {threat && (
              <span className="text-sm text-[#64748B] font-mono">
                Tehdit:{" "}
                <strong className="text-[#E2E8F0]">{threat.identified_threats.length}</strong>
              </span>
            )}
          </div>
          {threat
            ? <p className="text-[#E2E8F0] text-sm leading-relaxed max-w-3xl">{threat.executive_summary}</p>
            : <p className="text-[#64748B] text-sm">İstatistiksel analiz tamamlandı. Tehdit raporu bekleniyor…</p>
          }
        </div>
        {threat && (
          <a href={api.getPdfUrl(analysisId)} download className="btn-secondary text-sm flex-shrink-0">
            <Download size={15} /> PDF Raporu
          </a>
        )}
      </div>

      {/* Sekmeler */}
      <div className="flex gap-1 border-b border-[#1E3A5F]">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors -mb-px font-mono
              ${tab === t.id
                ? "border-[#00D4FF] text-[#00D4FF]"
                : "border-transparent text-[#64748B] hover:text-[#E2E8F0]"}`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Sekme içeriği */}
      {tab === "summary"    && <SummaryTab threat={threat} />}
      {tab === "threats"    && <ThreatsTab threat={threat} />}
      {tab === "statistics" && <StatisticsTab heuristic={heuristic} />}
      {tab === "raw"        && <RawTab analysis={analysis} />}
    </div>
  );
}

// ─── Sekme: Özet ──────────────────────────────────────────────────────────────

function SummaryTab({ threat }: { threat: ThreatReport | null }) {
  if (!threat) {
    return (
      <div className="card px-5 py-12 text-center text-[#64748B] text-sm font-mono">
        <Loader2 size={28} className="mx-auto mb-3 text-[#00D4FF] animate-spin" />
        Yapay zeka tehdit analizi bekleniyor…
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {threat.investigation_priority.length > 0 && (
        <StatsTable
          title="Araştırma Öncelikleri"
          rows={threat.investigation_priority}
          columns={[
            { key: "entity" as const, header: "#", render: (_v, _r) => null },
            {
              key: "entity" as const,
              header: "Varlık",
              render: (v) => <span className="font-mono text-xs text-[#00D4FF]">{String(v)}</span>,
            },
            { key: "reason" as const, header: "Sebep" },
          ]}
        />
      )}

      {threat.suggested_waf_rules.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-5 py-3.5 border-b border-[#1E3A5F] bg-[#132238]/50">
            <h3 className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest">
              Önerilen WAF Kuralları
            </h3>
          </div>
          <div className="p-5 space-y-3">
            {threat.suggested_waf_rules.map((rule, i) => (
              <div key={i} className="flex items-start gap-3 bg-[#020810] border border-[#1E3A5F] rounded-lg px-4 py-3">
                <span className="text-xs font-bold text-[#EF2B2D] mt-0.5 flex-shrink-0 font-mono">
                  {i + 1}
                </span>
                <code className="text-xs text-[#4ADE80] font-mono leading-relaxed break-all">
                  {rule}
                </code>
              </div>
            ))}
          </div>
        </div>
      )}

      {threat.false_positive_warnings.length > 0 && (
        <div className="card p-5 border-amber-800/40 bg-amber-950/30">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={15} className="text-amber-400" />
            <h3 className="text-sm font-semibold text-amber-300">
              Yanlış Pozitif Uyarıları
            </h3>
          </div>
          <ul className="space-y-2">
            {threat.false_positive_warnings.map((w, i) => (
              <li key={i} className="text-sm text-amber-200/80 flex items-start gap-2">
                <span className="text-amber-500 flex-shrink-0 mt-1">›</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Sekme: Tehditler ─────────────────────────────────────────────────────────

function ThreatsTab({ threat }: { threat: ThreatReport | null }) {
  if (!threat) {
    return (
      <div className="card px-5 py-12 text-center text-[#64748B] text-sm font-mono">
        <Loader2 size={28} className="mx-auto mb-3 text-[#00D4FF] animate-spin" />
        Tehdit listesi bekleniyor…
      </div>
    );
  }
  if (threat.identified_threats.length === 0) {
    return (
      <div className="card px-5 py-12 text-center text-[#64748B] text-sm font-mono">
        <CheckCircle2 size={32} className="mx-auto mb-3 text-emerald-400" />
        Önemli tehdit tespit edilmedi.
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {threat.identified_threats.map((t, i) => (
        <ThreatCard key={i} threat={t} index={i} />
      ))}
    </div>
  );
}

// ─── Sekme: İstatistikler ─────────────────────────────────────────────────────

function StatisticsTab({ heuristic }: { heuristic: HeuristicReport }) {
  const total = heuristic.total_events;
  const ACTION_COLORS: Record<string, string> = {
    block:     "bg-[#EF2B2D]",
    allow:     "bg-emerald-500",
    log:       "bg-[#64748B]",
    challenge: "bg-amber-500",
  };
  const ACTION_TR: Record<string, string> = {
    block:     "Engelle",
    allow:     "İzin Ver",
    log:       "Kaydet",
    challenge: "Meydan Oku",
  };

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-6">
        <StatsTable
          title="En Fazla İstek Atan IP'ler"
          rows={heuristic.top_source_ips}
          columns={[
            {
              key: "ip" as const,
              header: "IP Adresi",
              render: (v) => <span className="font-mono text-xs text-[#00D4FF]">{String(v)}</span>,
            },
            {
              key: "count" as const,
              header: "İstek",
              align: "right",
              render: (v) => Number(v).toLocaleString("tr-TR"),
            },
            {
              key: "percentage" as const,
              header: "Pay",
              align: "right",
              render: (v) => `${Number(v).toFixed(1)}%`,
            },
          ]}
        />
        <StatsTable
          title="En Fazla İstek Alan URI'ler"
          rows={heuristic.top_uris}
          columns={[
            {
              key: "value" as const,
              header: "URI",
              render: (v) => (
                <span className="font-mono text-xs text-[#00D4FF] truncate block max-w-xs">
                  {String(v)}
                </span>
              ),
            },
            {
              key: "count" as const,
              header: "İstek",
              align: "right",
              render: (v) => Number(v).toLocaleString("tr-TR"),
            },
          ]}
        />
        <StatsTable
          title="En Fazla İstek Gelen Ülkeler"
          rows={heuristic.top_countries}
          columns={[
            { key: "value" as const, header: "Ülke" },
            {
              key: "count" as const,
              header: "İstek",
              align: "right",
              render: (v) => Number(v).toLocaleString("tr-TR"),
            },
          ]}
        />
        {heuristic.top_rules_triggered.length > 0 && (
          <StatsTable
            title="En Çok Tetiklenen Kurallar"
            rows={heuristic.top_rules_triggered}
            columns={[
              {
                key: "rule_id" as const,
                header: "Kural ID",
                render: (v) => (
                  <span className="font-mono text-xs text-[#00D4FF]">{String(v)}</span>
                ),
              },
              {
                key: "rule_message" as const,
                header: "Mesaj",
                render: (v) => String(v ?? "—"),
              },
              {
                key: "count" as const,
                header: "Tetiklenme",
                align: "right",
                render: (v) => Number(v).toLocaleString("tr-TR"),
              },
            ]}
          />
        )}
      </div>

      {/* Eylem dağılımı */}
      <div className="card p-5">
        <h3 className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest mb-4">
          Eylem Dağılımı
        </h3>
        <div className="space-y-3">
          {Object.entries(heuristic.action_distribution).map(([action, count]) => {
            const pct = Math.round((count / total) * 100);
            return (
              <div key={action} className="flex items-center gap-4">
                <span className="text-xs font-bold uppercase tracking-widest text-[#64748B] w-24 text-right font-mono">
                  {ACTION_TR[action] ?? action}
                </span>
                <div className="flex-1 bg-[#132238] rounded-full h-2 border border-[#1E3A5F]">
                  <div
                    className={`h-2 rounded-full ${ACTION_COLORS[action] ?? "bg-[#64748B]"} transition-all duration-500`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-sm tabular-nums text-[#E2E8F0] w-28 text-right font-mono">
                  {count.toLocaleString("tr-TR")} ({pct}%)
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Anormallikler */}
      <div>
        <h3 className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest mb-4 flex items-center gap-2">
          <List size={15} /> Tespit Edilen Anormallikler
        </h3>
        <AnomalyList anomalies={heuristic.anomalies} />
      </div>
    </div>
  );
}

// ─── Sekme: Ham Veri ──────────────────────────────────────────────────────────

function RawTab({ analysis }: { analysis: AnalysisRead }) {
  return (
    <div className="space-y-4">
      {[
        { label: "Tehdit Raporu", data: analysis.threat_report },
        { label: "Buluşsal Analiz Raporu", data: analysis.heuristic_report },
      ].map(({ label, data }) => (
        <div key={label} className="card overflow-hidden">
          <div className="px-5 py-3.5 border-b border-[#1E3A5F] bg-[#132238]/50 flex items-center justify-between">
            <h3 className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest">{label}</h3>
            <button
              onClick={() => navigator.clipboard.writeText(JSON.stringify(data, null, 2))}
              className="text-xs text-[#64748B] hover:text-[#00D4FF] font-semibold font-mono transition-colors"
            >
              JSON Kopyala
            </button>
          </div>
          <pre className="text-xs text-[#4ADE80] font-mono p-5 overflow-auto max-h-96 bg-[#020810] leading-relaxed">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  );
}