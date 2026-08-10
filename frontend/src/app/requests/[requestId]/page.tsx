"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { requestsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatCost, formatDateTime, formatLatency } from "@/lib/format";

export default function RequestDetailPage({
  params,
}: {
  params: Promise<{ requestId: string }>;
}) {
  const { requestId } = use(params);
  const decodedId = decodeURIComponent(requestId);

  const detailQuery = useQuery({
    queryKey: ["request-detail", decodedId],
    queryFn: () => requestsApi.detail(decodedId),
  });

  const detail = detailQuery.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href="/requests"
          className="mb-1 inline-block text-sm text-muted-foreground hover:text-foreground hover:underline"
        >
          ← Back to requests
        </Link>
        <h1 className="break-all text-2xl font-semibold">{decodedId}</h1>
      </div>

      {detailQuery.isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : detailQuery.isError || !detail ? (
        <p className="text-sm text-destructive">Request not found.</p>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Summary
                <Badge variant={detail.status === "success" ? "secondary" : "destructive"}>
                  {detail.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <Field label="Provider" value={detail.provider} />
              <Field label="Model" value={detail.model} />
              <Field label="Environment" value={detail.environment ?? "—"} />
              <Field label="Application" value={detail.application_id ?? "unassigned"} />
              <Field label="Created" value={formatDateTime(detail.created_at)} />
              <Field label="Completed" value={formatDateTime(detail.completed_at)} />
              <Field label="Latency" value={formatLatency(detail.latency_ms)} />
              <Field label="Time to first token" value={formatLatency(detail.ttft_ms)} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tokens &amp; cost</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 md:grid-cols-3">
              <Field label="Input tokens" value={String(detail.input_tokens)} />
              <Field label="Output tokens" value={String(detail.output_tokens)} />
              <Field label="Total tokens" value={String(detail.total_tokens)} />
              <Field label="Input cost" value={formatCost(detail.input_cost)} />
              <Field label="Output cost" value={formatCost(detail.output_cost)} />
              <Field label="Total cost" value={formatCost(detail.total_cost)} />
            </CardContent>
          </Card>

          {detail.status !== "success" ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-destructive">Error</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <Field label="Type" value={detail.error_type ?? "—"} />
                <Field label="Code" value={detail.error_code ?? "—"} />
                <Field label="Message" value={detail.error_message ?? "—"} />
              </CardContent>
            </Card>
          ) : null}

          {Object.keys(detail.metadata ?? {}).length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Metadata</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="overflow-x-auto rounded-md bg-muted p-4 text-xs">
                  {JSON.stringify(detail.metadata, null, 2)}
                </pre>
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium uppercase text-muted-foreground">{label}</span>
      <span className="text-sm">{value}</span>
      <Separator className="mt-1" />
    </div>
  );
}
