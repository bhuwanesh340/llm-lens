"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { RangeFilters } from "@/lib/types";

const FILTER_KEYS = ["from", "to", "provider", "model", "application_id", "environment"] as const;

/**
 * Reads/writes the shared time-range + entity filters from the URL query
 * string so filter state is consistent and shareable across every
 * dashboard view (overview/usage/costs/models/requests/errors).
 */
export function useRangeFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const filters: RangeFilters = useMemo(() => {
    const result: RangeFilters = {};
    for (const key of FILTER_KEYS) {
      const value = searchParams.get(key);
      if (value) {
        result[key] = value;
      }
    }
    return result;
  }, [searchParams]);

  const setFilters = useCallback(
    (updates: Partial<RangeFilters>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const key of FILTER_KEYS) {
        const value = updates[key];
        if (value === undefined || value === "") {
          params.delete(key);
        } else {
          params.set(key, value);
        }
      }
      router.replace(`${pathname}?${params.toString()}`);
    },
    [pathname, router, searchParams],
  );

  const clearFilters = useCallback(() => {
    router.replace(pathname);
  }, [pathname, router]);

  return { filters, setFilters, clearFilters };
}
