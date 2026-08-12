"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { modelsApi } from "@/lib/api";
import { useRangeFilters } from "@/lib/use-range-filters";
import { FilterBar } from "@/components/filter-bar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCost, formatLatency, formatNumber, formatPercent } from "@/lib/format";

export default function ModelsPage() {
  const { filters, setFilters, clearFilters } = useRangeFilters();

  const modelsQuery = useQuery({
    queryKey: ["models", filters],
    queryFn: () => modelsApi.list(filters),
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Models</h1>
        <p className="text-muted-foreground">
          Per-model request volume, cost, latency, and error rate.
        </p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      <Card>
        <CardContent className="pt-6">
          {modelsQuery.isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : !modelsQuery.data || modelsQuery.data.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center text-sm">
              No model activity for this range.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead className="text-right">Requests</TableHead>
                  <TableHead className="text-right">Total cost</TableHead>
                  <TableHead className="text-right">Avg latency</TableHead>
                  <TableHead className="text-right">P95 latency</TableHead>
                  <TableHead className="text-right">Error rate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {modelsQuery.data.map((row) => (
                  <TableRow key={row.model}>
                    <TableCell className="font-medium">
                      <Link
                        href={`/models/${encodeURIComponent(row.model)}`}
                        className="text-primary hover:underline"
                      >
                        {row.model}
                      </Link>
                    </TableCell>
                    <TableCell>{row.provider}</TableCell>
                    <TableCell className="text-right">{formatNumber(row.request_count)}</TableCell>
                    <TableCell className="text-right">{formatCost(row.total_cost)}</TableCell>
                    <TableCell className="text-right">
                      {formatLatency(row.avg_latency_ms)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatLatency(row.p95_latency_ms)}
                    </TableCell>
                    <TableCell className="text-right">{formatPercent(row.error_rate)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
