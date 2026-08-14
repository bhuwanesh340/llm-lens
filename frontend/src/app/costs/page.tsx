"use client";

import { useQuery } from "@tanstack/react-query";
import { costsApi } from "@/lib/api";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatCost, formatNumber } from "@/lib/format";
import type { CostBreakdownItem } from "@/lib/types";

export default function CostsPage() {
  const { filters, setFilters, clearFilters } = useRangeFilters();

  const byModelQuery = useQuery({
    queryKey: ["costs-by-model", filters],
    queryFn: () => costsApi.byModel(filters),
  });
  const byProviderQuery = useQuery({
    queryKey: ["costs-by-provider", filters],
    queryFn: () => costsApi.byProvider(filters),
  });
  const byProjectQuery = useQuery({
    queryKey: ["costs-by-project", filters],
    queryFn: () => costsApi.byProject(filters),
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Costs</h1>
        <p className="text-muted-foreground">
          Spend broken down by model, provider, and project. Requests with unknown pricing are
          tracked separately and excluded from totals.
        </p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      <Card>
        <CardContent className="pt-6">
          <Tabs defaultValue="by-model">
            <TabsList>
              <TabsTrigger value="by-model">By model</TabsTrigger>
              <TabsTrigger value="by-provider">By provider</TabsTrigger>
              <TabsTrigger value="by-project">By project</TabsTrigger>
            </TabsList>
            <TabsContent value="by-model">
              <CostBreakdownTable rows={byModelQuery.data} isLoading={byModelQuery.isLoading} />
            </TabsContent>
            <TabsContent value="by-provider">
              <CostBreakdownTable
                rows={byProviderQuery.data}
                isLoading={byProviderQuery.isLoading}
              />
            </TabsContent>
            <TabsContent value="by-project">
              <CostBreakdownTable
                rows={byProjectQuery.data}
                isLoading={byProjectQuery.isLoading}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function CostBreakdownTable({
  rows,
  isLoading,
}: {
  rows?: CostBreakdownItem[];
  isLoading: boolean;
}) {
  if (isLoading) return <Skeleton className="h-40 w-full" />;
  if (!rows || rows.length === 0) {
    return (
      <p className="text-muted-foreground py-8 text-center text-sm">No data for this range.</p>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Key</TableHead>
          <TableHead className="text-right">Requests</TableHead>
          <TableHead className="text-right">Total cost</TableHead>
          <TableHead className="text-right">Unknown-cost requests</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.key}>
            <TableCell className="font-medium">{row.key}</TableCell>
            <TableCell className="text-right">{formatNumber(row.request_count)}</TableCell>
            <TableCell className="text-right">{formatCost(row.total_cost)}</TableCell>
            <TableCell className="text-right">
              {row.unknown_cost_count > 0 ? (
                <span className="text-amber-600">{row.unknown_cost_count}</span>
              ) : (
                0
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
