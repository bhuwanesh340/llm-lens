"use client";

import { useQuery } from "@tanstack/react-query";
import { usageApi } from "@/lib/api";
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
import { formatNumber } from "@/lib/format";

export default function UsagePage() {
  const { filters, setFilters, clearFilters } = useRangeFilters();

  const summaryQuery = useQuery({
    queryKey: ["usage-summary", filters],
    queryFn: () => usageApi.summary(filters),
  });
  const byModelQuery = useQuery({
    queryKey: ["usage-by-model", filters],
    queryFn: () => usageApi.byModel(filters),
  });
  const byProviderQuery = useQuery({
    queryKey: ["usage-by-provider", filters],
    queryFn: () => usageApi.byProvider(filters),
  });

  const summary = summaryQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Usage</h1>
        <p className="text-muted-foreground">Token and request volume across providers and models.</p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: "Requests", value: summary ? formatNumber(summary.total_requests) : null },
          { label: "Input tokens", value: summary ? formatNumber(summary.input_tokens) : null },
          { label: "Output tokens", value: summary ? formatNumber(summary.output_tokens) : null },
          { label: "Total tokens", value: summary ? formatNumber(summary.total_tokens) : null },
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
          <Tabs defaultValue="by-model">
            <TabsList>
              <TabsTrigger value="by-model">By model</TabsTrigger>
              <TabsTrigger value="by-provider">By provider</TabsTrigger>
            </TabsList>
            <TabsContent value="by-model">
              <UsageBreakdownTable rows={byModelQuery.data} isLoading={byModelQuery.isLoading} />
            </TabsContent>
            <TabsContent value="by-provider">
              <UsageBreakdownTable
                rows={byProviderQuery.data}
                isLoading={byProviderQuery.isLoading}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function UsageBreakdownTable({
  rows,
  isLoading,
}: {
  rows?: { key: string; input_tokens: number; output_tokens: number; total_tokens: number; request_count: number; avg_tokens_per_request: number }[];
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
          <TableHead className="text-right">Requests</TableHead>
          <TableHead className="text-right">Input tokens</TableHead>
          <TableHead className="text-right">Output tokens</TableHead>
          <TableHead className="text-right">Total tokens</TableHead>
          <TableHead className="text-right">Avg tokens/req</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.key}>
            <TableCell className="font-medium">{row.key}</TableCell>
            <TableCell className="text-right">{formatNumber(row.request_count)}</TableCell>
            <TableCell className="text-right">{formatNumber(row.input_tokens)}</TableCell>
            <TableCell className="text-right">{formatNumber(row.output_tokens)}</TableCell>
            <TableCell className="text-right">{formatNumber(row.total_tokens)}</TableCell>
            <TableCell className="text-right">{row.avg_tokens_per_request.toFixed(1)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
