"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image";
import { Plus, Clock, CheckCircle2, XCircle, Loader2, FileText, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { ThreatLevelBadge } from "@/components/ThreatLevelBadge";
import type { AnalysisRead } from "@/types";

const STATUS_ICON: Record<string, React.ReactNode> = {
  pending:    <Clock size={14} className="text-[#64748B]" />,
  processing: <Loader2 size={14} className="text-[#00D4FF] animate-spin" />,
  completed:  <CheckCircle2 size={14} className="text-emerald-400" />,
  failed:     <XCircle size={14} className="text-[#EF2B2D]" />,
};

const STATUS_TR: Record<string, string> = {
  pending:    "Bekliyor",
  processing: "İşleniyor",
  completed:  "Tamamlandı",
  failed:     "Başarısız",
};

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analyses"],
    queryFn: () => api.listAnalyses().then((r) => r.data),
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const hasActive = items.some(
        (a: AnalysisRead) => a.status === "pending" || a.status === "processing"
      );
      return hasActive ? 3000 : false;
    },
  });

  return (
    <div className="min-h-screen bg-[#060D17]">
      {/* NAV */}
      <nav className="nav-dark">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
              <Image src="/cassandra-logo.png" alt="Cassandra" width={32} height={32} className="w-full h-full object-cover" />
            </div>
            <div>
              <span className="font-bold text-[#E2E8F0] text-sm leading-none block">
                Cassandra CloudSec Agent
              </span>
              <span className="text-[10px] text-[#00D4FF] font-mono tracking-widest uppercase leading-none">
                Kontrol Paneli
              </span>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/upload" className="btn-primary text-sm">
              <Plus size={15} /> Yeni Analiz
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-8">
          <p className="section-title">Geçmiş Analizler</p>
          <h1 className="text-2xl font-bold text-[#E2E8F0]">Analiz Geçmişi</h1>
          <p className="text-[#64748B] mt-1 text-sm">Log analiz geçmişiniz ve tehdit raporlarınız</p>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-24 gap-3 text-[#64748B]">
            <Loader2 size={22} className="animate-spin text-[#00D4FF]" />
            <span className="text-sm font-mono">Analizler yükleniyor…</span>
          </div>
        )}

        {error && (
          <div className="card px-6 py-5 border-[#EF2B2D]/30 bg-[#EF2B2D]/5 flex items-center gap-3">
            <AlertTriangle size={18} className="text-[#EF2B2D]" />
            <p className="text-sm text-[#EF2B2D]">Analizler yüklenemedi. Lütfen sayfayı yenileyin.</p>
          </div>
        )}

        {data && data.items.length === 0 && (
          <div className="card px-6 py-16 text-center card-hover">
            <FileText size={40} className="text-[#1E3A5F] mx-auto mb-4" />
            <p className="text-base font-semibold text-[#E2E8F0] mb-2">Henüz analiz yok</p>
            <p className="text-sm text-[#64748B] mb-6">
              İlk tehdit raporunuzu almak için bir Cloudflare log dosyası yükleyin.
            </p>
            <Link href="/upload" className="btn-primary">
              <Plus size={15} /> Log Dosyası Yükle
            </Link>
          </div>
        )}

        {data && data.items.length > 0 && (
          <div className="space-y-3">
            {data.items.map((a: AnalysisRead) => (
              <Link
                key={a.id}
                href={`/analyses/${a.id}`}
                className="card card-hover p-5 flex items-center gap-5 hover:border-[#00D4FF]/30 transition-all duration-200 block"
              >
                <div className="w-10 h-10 bg-[#132238] rounded-xl flex items-center justify-center flex-shrink-0 border border-[#1E3A5F]">
                  {STATUS_ICON[a.status]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-semibold text-[#E2E8F0] text-sm font-mono">
                      Analiz #{a.id}
                    </span>
                    <span className="text-xs text-[#64748B]">{STATUS_TR[a.status] ?? a.status}</span>
                    {a.status === "processing" && (
                      <span className="text-xs bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/20 px-2 py-0.5 rounded-full font-semibold">
                        İşleniyor
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[#64748B] font-mono">
                    {a.completed_at
                      ? `Tamamlandı: ${new Date(a.completed_at).toLocaleString("tr-TR")}`
                      : a.started_at
                      ? `Başladı: ${new Date(a.started_at).toLocaleString("tr-TR")}`
                      : "Kuyruğa alındı"}
                  </p>
                </div>
                {a.threat_report && (
                  <ThreatLevelBadge level={a.threat_report.threat_level} size="sm" />
                )}
              </Link>
            ))}
          </div>
        )}

        {data && data.total > data.items.length && (
          <p className="text-center text-sm text-[#64748B] mt-6 font-mono">
            {data.items.length} / {data.total} analiz gösteriliyor
          </p>
        )}
      </main>
    </div>
  );
}