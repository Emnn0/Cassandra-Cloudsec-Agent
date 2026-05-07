import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Shield, Zap, FileSearch, Download, Lock, Activity } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#060D17]">
      {/* NAV */}
      <nav className="nav-dark">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg overflow-hidden flex-shrink-0">
              <Image src="/cassandra-logo.png" alt="Cassandra" width={36} height={36} className="w-full h-full object-cover" />
            </div>
            <div>
              <span className="font-bold text-[#E2E8F0] text-sm tracking-tight leading-none block">
                Cassandra CloudSec Agent
              </span>
              <span className="text-[10px] text-[#00D4FF] font-mono tracking-widest uppercase leading-none">
                Bulut Güvenlik Analiz
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/sign-in"
              className="text-sm font-semibold text-[#64748B] hover:text-[#E2E8F0] transition-colors px-4 py-2"
            >
              Giriş Yap
            </Link>
            <Link href="/sign-up" className="btn-primary text-sm">
              Başla <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 bg-[#00D4FF]/10 text-[#00D4FF] text-xs font-bold px-3.5 py-1.5 rounded-full border border-[#00D4FF]/20 mb-8 uppercase tracking-widest">
          <Activity size={12} /> Yapay Zeka Destekli Güvenlik İstihbaratı
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold text-[#E2E8F0] tracking-tight leading-none mb-6">
          WAF loglarını
          <br />
          <span className="text-[#00D4FF]">tehdit istihbaratına</span>
          <br />
          <span className="text-[#EF2B2D]">dönüştür</span>
        </h1>
        <p className="text-xl text-[#64748B] max-w-2xl mx-auto mb-10 leading-relaxed">
          Cloudflare güvenlik duvarı loglarınızı yükleyin. Cassandra trafik desenlerini analiz eder,
          tehditleri tespit eder ve iki dakika içinde profesyonel bir PDF raporu sunar.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link href="/sign-up" className="btn-primary px-8 py-3.5 text-base">
            Analizi Başlat <ArrowRight size={17} />
          </Link>
          <Link href="/sign-in" className="btn-secondary px-8 py-3.5 text-base">
            Giriş Yap
          </Link>
        </div>
      </section>

      {/* FEATURES */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div key={f.title} className="card card-hover p-6 group">
              <div className="w-11 h-11 bg-[#132238] rounded-xl flex items-center justify-center mb-4 border border-[#1E3A5F] group-hover:border-[#00D4FF]/30 transition-colors">
                <f.Icon size={22} className="text-[#00D4FF]" />
              </div>
              <h3 className="font-bold text-[#E2E8F0] mb-2">{f.title}</h3>
              <p className="text-sm text-[#64748B] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-[#0D1B2E] border-y border-[#1E3A5F] py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="section-title text-center mb-2">Nasıl Çalışır</p>
          <h2 className="text-3xl font-bold text-[#E2E8F0] mb-4">Log dosyasından rapora üç adım</h2>
          <p className="text-[#64748B] mb-12">Hızlı, güvenli ve tamamen otomatik analiz süreci.</p>
          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((s, i) => (
              <div key={s.title} className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#EF2B2D] text-white font-black text-lg flex items-center justify-center mx-auto mb-4 shadow-glow-red">
                  {i + 1}
                </div>
                <h3 className="font-bold text-[#E2E8F0] mb-2">{s.title}</h3>
                <p className="text-sm text-[#64748B]">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-2xl mx-auto px-6 py-24 text-center">
        <div className="w-14 h-14 bg-[#EF2B2D]/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-[#EF2B2D]/20">
          <Lock size={28} className="text-[#EF2B2D]" />
        </div>
        <h2 className="text-3xl font-bold text-[#E2E8F0] mb-4">Altyapınızı korumaya hazır mısınız?</h2>
        <p className="text-[#64748B] mb-8">
          Ham log verilerini net, uygulanabilir tehdit istihbaratına dönüştürmek için
          Cassandra CloudSec Agent&apos;ı kullanmaya başlayın.
        </p>
        <Link href="/sign-up" className="btn-primary px-10 py-3.5 text-base">
          Ücretsiz Başla <ArrowRight size={17} />
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#1E3A5F] py-8 px-6 bg-[#0D1B2E]">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-[#64748B]">
          <div className="flex items-center gap-2.5">
            <div className="w-5 h-5 rounded overflow-hidden flex-shrink-0">
              <Image src="/cassandra-logo.png" alt="Cassandra" width={20} height={20} className="w-full h-full object-cover" />
            </div>
            <span className="font-mono text-xs">Cassandra CloudSec Agent © {new Date().getFullYear()}</span>
          </div>
          <span className="text-xs font-mono text-[#1E3A5F] uppercase tracking-widest">Gizli &amp; Tescilli</span>
        </div>
      </footer>
    </div>
  );
}

const FEATURES = [
  {
    title: "Anlık Tehdit Tespiti",
    desc: "İstatistiksel buluşsal yöntemler; IP baskınlığını, kural sıcak noktalarını, bot parmak izlerini ve trafik artışlarını saniyeler içinde tespit eder.",
    Icon: Zap,
  },
  {
    title: "Yapay Zeka Destekli Analiz",
    desc: "Claude; anormallikleri analiz eder, bulguları OWASP Top 10 ile eşler ve özel Cloudflare WAF kural önerileri üretir.",
    Icon: FileSearch,
  },
  {
    title: "Yönetici PDF Raporları",
    desc: "Kapak sayfası, tehdit kartları, istatistiksel ek ve güven skorları içeren profesyonel, yazdırmaya hazır raporlar.",
    Icon: Download,
  },
];

const STEPS = [
  {
    title: "Log Dosyanızı Yükleyin",
    desc: "Cloudflare NDJSON güvenlik duvarı veya HTTP log dosyanızı sürükleyip bırakın. 500MB'a kadar desteklenir.",
  },
  {
    title: "Yapay Zeka Veriyi Analiz Eder",
    desc: "Sistemimiz buluşsal analiz çalıştırır ve istatistiksel özeti derin tehdit analizi için Claude'a iletir.",
  },
  {
    title: "Raporunuzu İndirin",
    desc: "Uygulanabilir WAF kuralları ve yöneticiye hazır PDF içeren yapılandırılmış tehdit raporu alın.",
  },
];