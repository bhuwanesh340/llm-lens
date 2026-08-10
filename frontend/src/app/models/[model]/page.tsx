"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { modelsApi } from "@/lib/api";
import { useRangeFilters } from "@/lib/use-range-filters";
import { FilterBar } from "@/components/filter-bar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCost, formatLatency, formatNumber, formatPercent } from "@/lib/format";

export default function ModelDetailPage({
  params,
}: {
  params: Promise<{ model: string }>;
}) {
  const { model } = use(params);
  const modelName = decodeURIComponent(model);
  const { filters, setFilters, clearFilters } = useRangeFilters();

  const detailQuery = useQuery({
    queryKey: ["model-detail", modelName, filters],
    queryFn: () => modelsApi.detail(modelName, filters),
  });

  const detail = detailQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/models"
            className="mb-1 inline-block text-sm text-muted-foreground hover:text-foreground hover:underline"
          >
            ← Back to models
          </Link>
          <h1 className="text-2xl font-semibold">{modelName}</h1>
          {detail ? <p className="text-muted-foreground">Provider: {detail.provider}</p> : null}
        </div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      {detailQuery.isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : detailQuery.isError ? (
        <p className="text-sm text-destructive">No requests found for this model in this range.</p>
      ) : detail ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            { label: "Requests", value: formatNumber(detail.request_count) },
            { label: "Total tokens", value: formatNumber(detail.total_tokens) },
            { label: "Total cost", value: formatCost(detail.total_cost) },
            {
              label: "Avg cost/request",
              value: formatCost(detail.avg_cost_per_request),
            },
            { label: "Avg latency", value: formatLatency(detail.avg_latency_ms) },
            { label: "P95 latency", value: formatLatency(detail.p95_latency_ms) },
            { label: "Error rate", value: formatPercent(detail.error_rate) },
            { label: "Unknown-cost requests", value: formatNumber(detail.unknown_cost_count) },
          ].map((stat) => (
            <Card key={stat.label}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{stat.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}
