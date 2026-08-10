"use client";

import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/lib/api";

/** Reads current session auth status. Used by the dashboard AuthGuard and login page. */
export function useSession() {
  return useQuery({
    queryKey: ["session"],
    queryFn: () => authApi.session(),
    staleTime: 60_000,
  });
}
