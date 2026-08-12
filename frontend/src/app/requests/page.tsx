"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { requestsApi } from "@/lib/api";
import { useRangeFilters } from "@/lib/use-range-filters";
import { FilterBar } from "@/components/filter-bar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCost, formatDateTime, formatLatency } from "@/lib/format";
import { useState } from "react";

export default function RequestsPage() {
  const { filters, setFilters, clearFilters } = useRangeFilters();
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const requestsQuery = useQuery({
    queryKey: ["requests", filters, page],
    queryFn: () => requestsApi.list(filters, { page, page_size: pageSize }),
  });

  const data = requestsQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Requests</h1>
        <p className="text-muted-foreground">
          Browse individual LLM requests. No prompt/response content is stored.
        </p>
      </div>

      <FilterBar
        filters={filters}
        onChange={(updates) => {
          setPage(1);
          setFilters(updates);
        }}
        onClear={() => {
          setPage(1);
          clearFilters();
        }}
      />

      <Card>
        <CardContent className="pt-6">
          {requestsQuery.isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : !data || data.items.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center text-sm">
              No requests for this range.
            </p>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Created</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Tokens</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead className="text-right">Latency</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Link
                          href={`/requests/${encodeURIComponent(item.request_id)}`}
                          className="text-primary hover:underline"
                        >
                          {formatDateTime(item.created_at)}
                        </Link>
                      </TableCell>
                      <TableCell>{item.provider}</TableCell>
                      <TableCell>{item.model}</TableCell>
                      <TableCell>
                        <Badge variant={item.status === "success" ? "secondary" : "destructive"}>
                          {item.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">{item.total_tokens}</TableCell>
                      <TableCell className="text-right">{formatCost(item.total_cost)}</TableCell>
                      <TableCell className="text-right">{formatLatency(item.latency_ms)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-muted-foreground text-sm">
                  Page {data.meta.page} of {data.meta.total_pages} ({data.meta.total_items} total)
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= data.meta.total_pages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
