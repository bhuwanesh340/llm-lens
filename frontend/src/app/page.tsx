"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { overviewApi, costsApi } from "@/lib/api";
import { useRangeFilters } from "@/lib/use-range-filters";
import { FilterBar } from "@/components/filter-bar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCost, formatLatency, formatNumber, formatPercent } from "@/lib/format";

export default function DashboardPage() {
  const { filters, setFilters, clearFilters } = useRangeFilters();

  const overviewQuery = useQuery({
    queryKey: ["overview", filters],
    queryFn: () => overviewApi.get(filters),
  });

  const timeseriesQuery = useQuery({
    queryKey: ["costs-timeseries", filters],
    queryFn: () => costsApi.timeseries(filters),
  });

  const overview = overviewQuery.data;

  const stats = [
    { label: "Total requests", value: overview ? formatNumber(overview.total_requests) : null },
    { label: "Total cost", value: overview ? formatCost(overview.total_cost) : null },
    { label: "Total tokens", value: overview ? formatNumber(overview.total_tokens) : null },
    { label: "Avg latency", value: overview ? formatLatency(overview.avg_latency_ms) : null },
    { label: "Error rate", value: overview ? formatPercent(overview.error_rate) : null },
    { label: "Active models", value: overview ? formatNumber(overview.active_models) : null },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-muted-foreground">Overview of LLM usage, cost, and reliability.</p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      {overview?.unknown_cost_count ? (
        <p className="text-sm text-amber-600">
          {overview.unknown_cost_count} request(s) have unknown pricing and are excluded from
          cost totals.
        </p>
      ) : null}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stat.value === null ? (
                <Skeleton className="h-7 w-20" />
              ) : (
                <p className="text-2xl font-semibold">{stat.value}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cost over time</CardTitle>
        </CardHeader>
        <CardContent className="h-72">
          {timeseriesQuery.isLoading ? (
            <Skeleton className="h-full w-full" />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={(timeseriesQuery.data ?? []).map((point) => ({
                  date: new Date(point.date).toLocaleDateString(),
                  cost: point.total_cost ? Number(point.total_cost) : 0,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="cost"
                  stroke="var(--chart-1, #6366f1)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
