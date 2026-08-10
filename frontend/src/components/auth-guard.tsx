"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/use-session";
import { Skeleton } from "@/components/ui/skeleton";

/** Redirects to /login unless a valid admin session cookie is present. */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { data, isLoading, isError } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && (isError || !data?.authenticated)) {
      router.replace("/login");
    }
  }, [isLoading, isError, data, router]);

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-7xl flex-col gap-4 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isError || !data?.authenticated) {
    return null;
  }

  return <>{children}</>;
}
