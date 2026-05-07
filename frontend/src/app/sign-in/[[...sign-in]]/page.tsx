import Image from "next/image";
import Link from "next/link";
import { SignIn } from "@clerk/nextjs";
import { KeyRound } from "lucide-react";

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";
const clerkReady =
  publishableKey.startsWith("pk_test_") || publishableKey.startsWith("pk_live_");

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-[#060D17] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo + Başlık */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl overflow-hidden flex-shrink-0">
              <Image
                src="/cassandra-logo.png"
                alt="Cassandra"
                width={40}
                height={40}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="text-left">
              <span className="font-bold text-[#E2E8F0] text-lg leading-none block">
                Cassandra CloudSec Agent
              </span>
              <span className="text-[10px] text-[#00D4FF] font-mono tracking-widest uppercase leading-none">
                Bulut Güvenlik Analiz
              </span>
            </div>
          </div>
          <p className="text-[#64748B] text-sm">Analizlerinize erişmek için giriş yapın</p>
        </div>

        {clerkReady ? (
          <SignIn routing="path" path="/sign-in" afterSignInUrl="/dashboard" />
        ) : (
          <div className="card p-8 text-center space-y-4 border-[#1E3A5F]">
            <div className="w-12 h-12 bg-[#00D4FF]/10 rounded-full flex items-center justify-center mx-auto border border-[#00D4FF]/20">
              <KeyRound size={22} className="text-[#00D4FF]" />
            </div>
            <h2 className="text-[#E2E8F0] font-semibold">Kimlik Doğrulama Yapılandırılmamış</h2>
            <p className="text-sm text-[#64748B] leading-relaxed">
              Clerk kimlik doğrulama henüz yapılandırılmamış. Geliştirme ortamında
              doğrudan panele erişebilirsiniz.
            </p>
            <Link href="/dashboard" className="btn-accent w-full justify-center">
              Panele Git
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}