"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { authApi } from "@/lib/api";
import { Button } from "@/components/ui/button";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/usage", label: "Usage" },
  { href: "/costs", label: "Costs" },
  { href: "/models", label: "Models" },
  { href: "/requests", label: "Requests" },
  { href: "/projects", label: "Projects" },
  { href: "/errors", label: "Errors" },
];

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();

  async function handleLogout() {
    try {
      await authApi.logout();
      queryClient.clear();
      router.push("/login");
    } catch {
      toast.error("Failed to log out");
    }
  }

  return (
    <header className="bg-card/70 border-border sticky top-0 z-50 border-b backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <span
              aria-hidden
              className="from-primary to-accent size-5 rounded-md bg-gradient-to-br"
            />
            LLM Lens
          </span>
          <nav className="flex items-center gap-1">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={pathname === link.href ? "page" : undefined}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  pathname === link.href
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          Log out
        </Button>
      </div>
    </header>
  );
}
