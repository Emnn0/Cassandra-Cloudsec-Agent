import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Clerk keys must start with pk_test_ or pk_live_ — anything else means
// the app is running without auth configured (local dev / CI).
const CLERK_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";
const CLERK_ACTIVE =
  CLERK_KEY.startsWith("pk_test_") || CLERK_KEY.startsWith("pk_live_");

// Routes that require authentication when Clerk is configured
const PROTECTED = ["/dashboard", "/upload", "/analyses"];

export async function middleware(req: NextRequest) {
  if (!CLERK_ACTIVE) return NextResponse.next();

  // Lazy-import so the module is never evaluated when Clerk is not configured
  const { clerkMiddleware, createRouteMatcher } = await import(
    "@clerk/nextjs/server"
  );
  const isProtected = createRouteMatcher(PROTECTED.map((p) => `${p}(.*)`));
  return clerkMiddleware((auth) => {
    if (isProtected(req)) auth().protect();
  })(req, {} as never);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};