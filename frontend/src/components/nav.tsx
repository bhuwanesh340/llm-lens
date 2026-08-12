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
  { href: "/applications", label: "Applications" },
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
    <header className="bg-card border-b">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3">
        <div className="flex items-center gap-6">
          <span className="text-lg font-semibold">LLM Lens</span>
          <nav className="flex items-center gap-1">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "hover:bg-accent hover:text-accent-foreground rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  pathname === link.href
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground",
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
