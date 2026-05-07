import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { Providers } from "@/lib/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: { default: "Cassandra CloudSec Agent", template: "%s · Cassandra CloudSec Agent" },
  description: "Yapay Zeka Destekli Bulut Güvenlik & WAF Log Analiz Platformu",
};

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";
const clerkReady =
  publishableKey.startsWith("pk_test_") || publishableKey.startsWith("pk_live_");

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const content = (
    <html lang="tr" className={inter.variable}>
      <body className="font-sans antialiased bg-[#060D17] text-[#E2E8F0]">
        <Providers>{children}</Providers>
      </body>
    </html>
  );

  return clerkReady ? (
    <ClerkProvider>{content}</ClerkProvider>
  ) : (
    content
  );
}