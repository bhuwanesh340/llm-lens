"use client";

import { usePathname } from "next/navigation";
import { Nav } from "@/components/nav";
import { AuthGuard } from "@/components/auth-guard";

const PUBLIC_ROUTES = new Set(["/login"]);

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (PUBLIC_ROUTES.has(pathname)) {
    return <>{children}</>;
  }

  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col bg-muted/30">
        <Nav />
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">{children}</main>
      </div>
    </AuthGuard>
  );
}
