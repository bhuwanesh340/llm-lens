"use client";

import { useQuery } from "@tanstack/react-query";
import { errorsApi } from "@/lib/api";
import { useRangeFilters } from "@/lib/use-range-filters";
import { FilterBar } from "@/components/filter-bar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { formatNumber, formatPercent } from "@/lib/format";
import type { ErrorBreakdownItem } from "@/lib/types";

export default function ErrorsPage() {
  const { filters, setFilters, clearFilters } = useRangeFilters();

  const summaryQuery = useQuery({
    queryKey: ["errors-summary", filters],
    queryFn: () => errorsApi.summary(filters),
  });
  const byProviderQuery = useQuery({
    queryKey: ["errors-by-provider", filters],
    queryFn: () => errorsApi.byProvider(filters),
  });
  const byModelQuery = useQuery({
    queryKey: ["errors-by-model", filters],
    queryFn: () => errorsApi.byModel(filters),
  });
  const byCodeQuery = useQuery({
    queryKey: ["errors-by-code", filters],
    queryFn: () => errorsApi.byCode(filters),
  });

  const summary = summaryQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Errors</h1>
        <p className="text-muted-foreground">Failure rates broken down by provider, model, and error code.</p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total requests", value: summary ? formatNumber(summary.total_requests) : null },
          { label: "Errors", value: summary ? formatNumber(summary.error_count) : null },
          { label: "Error rate", value: summary ? formatPercent(summary.error_rate) : null },
        ].map((stat) => (
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
        <CardContent className="pt-6">
          <Tabs defaultValue="by-provider">
            <TabsList>
              <TabsTrigger value="by-provider">By provider</TabsTrigger>
              <TabsTrigger value="by-model">By model</TabsTrigger>
              <TabsTrigger value="by-code">By error code</TabsTrigger>
            </TabsList>
            <TabsContent value="by-provider">
              <ErrorBreakdownTable
                rows={byProviderQuery.data}
                isLoading={byProviderQuery.isLoading}
              />
            </TabsContent>
            <TabsContent value="by-model">
              <ErrorBreakdownTable rows={byModelQuery.data} isLoading={byModelQuery.isLoading} />
            </TabsContent>
            <TabsContent value="by-code">
              <ErrorBreakdownTable rows={byCodeQuery.data} isLoading={byCodeQuery.isLoading} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function ErrorBreakdownTable({
  rows,
  isLoading,
}: {
  rows?: ErrorBreakdownItem[];
  isLoading: boolean;
}) {
  if (isLoading) return <Skeleton className="h-40 w-full" />;
  if (!rows || rows.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No data for this range.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Key</TableHead>
          <TableHead className="text-right">Errors</TableHead>
          <TableHead className="text-right">Total requests</TableHead>
          <TableHead className="text-right">Error rate</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.key}>
            <TableCell className="font-medium">{row.key}</TableCell>
            <TableCell className="text-right">{formatNumber(row.error_count)}</TableCell>
            <TableCell className="text-right">{formatNumber(row.total_count)}</TableCell>
            <TableCell className="text-right">{formatPercent(row.error_rate)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
