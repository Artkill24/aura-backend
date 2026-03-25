import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/analyze", "/dashboard", "/result"];

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const isProtected = PROTECTED.some(p => path.startsWith(p));

  if (!isProtected) return NextResponse.next();

  // Controlla cookie Supabase auth
  const token = request.cookies.get("sb-vtqrojazozbqbhgozbor-auth-token")?.value
    || request.cookies.get("supabase-auth-token")?.value
    || [...request.cookies.getAll()].find(c => c.name.includes("auth-token"))?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", path);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/analyze/:path*", "/dashboard/:path*", "/result/:path*"],
};
