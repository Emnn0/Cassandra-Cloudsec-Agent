"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft } from "lucide-react";
import { FileUploader } from "@/components/FileUploader";

export default function UploadPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#060D17]">
      <nav className="nav-dark">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-4">
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
            <span className="font-bold text-[#E2E8F0] text-sm">Cassandra CloudSec Agent</span>
          </div>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-6 py-14">
        <div className="mb-10">
          <p className="section-title">Yeni Analiz</p>
          <h1 className="text-2xl font-bold text-[#E2E8F0] mb-2">Log Dosyası Yükle</h1>
          <p className="text-[#64748B] text-sm leading-relaxed">
            NDJSON formatında Cloudflare Güvenlik Duvarı ve HTTP Erişim loglarını destekler.
            Dosyalar S3&apos;e güvenli şekilde yüklenir ve otomatik olarak analiz edilir.
          </p>
        </div>

        <FileUploader onComplete={(id) => router.push(`/analyses/${id}`)} />

        <div className="mt-8 bg-[#0D1B2E] border border-[#1E3A5F] rounded-xl p-5">
          <p className="text-xs font-bold text-[#00D4FF] uppercase tracking-widest mb-3">
            Desteklenen Formatlar
          </p>
          <ul className="space-y-2 text-sm text-[#64748B]">
            <li className="flex items-start gap-2">
              <span className="font-mono text-xs bg-[#132238] border border-[#1E3A5F] text-[#00D4FF] px-1.5 py-0.5 rounded mt-0.5">
                .ndjson
              </span>
              <span>Cloudflare Güvenlik Duvarı Olayları (GraphQL dışa aktarma)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono text-xs bg-[#132238] border border-[#1E3A5F] text-[#00D4FF] px-1.5 py-0.5 rounded mt-0.5">
                .log/.json
              </span>
              <span>Cloudflare HTTP Erişim Logları (Logpush formatı)</span>
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}