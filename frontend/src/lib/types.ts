/**
 * TypeScript types mirroring the backend Pydantic response schemas
 * (backend/app/schemas/analytics.py, requests.py, applications.py, common.py).
 */

export interface PageMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

export interface ErrorDetail {
  code: string;
  message: string;
  request_id: string | null;
}

export interface ErrorEnvelope {
  error: ErrorDetail;
}

export interface OverviewResponse {
  total_requests: number;
  total_cost: string | null;
  unknown_cost_count: number;
  total_tokens: number;
  avg_latency_ms: number | null;
  error_rate: number;
  active_models: number;
}

export interface CostBreakdownItem {
  key: string;
  total_cost: string | null;
  unknown_cost_count: number;
  request_count: number;
}

export interface CostTimeseriesItem {
  date: string;
  total_cost: string | null;
  unknown_cost_count: number;
  request_count: number;
}

export interface UsageSummaryResponse {
  total_requests: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  avg_tokens_per_request: number;
}

export interface UsageTimeseriesItem {
  date: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
}

export interface UsageBreakdownItem {
  key: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
  avg_tokens_per_request: number;
}

export interface ErrorsSummaryResponse {
  total_requests: number;
  error_count: number;
  error_rate: number;
}

export interface ErrorBreakdownItem {
  key: string;
  error_count: number;
  total_count: number;
  error_rate: number;
}

export interface ModelSummaryItem {
  model: string;
  provider: string;
  request_count: number;
  total_tokens: number;
  total_cost: string | null;
  unknown_cost_count: number;
  avg_cost_per_request: string | null;
  avg_latency_ms: number | null;
  p95_latency_ms: number | null;
  error_rate: number;
}

export type ModelDetailResponse = ModelSummaryItem;

export interface RequestListItem {
  id: string;
  request_id: string;
  created_at: string;
  provider: string;
  model: string;
  application_id: string | null;
  environment: string | null;
  status: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost: string | null;
  latency_ms: number;
}

export interface RequestDetail extends RequestListItem {
  completed_at: string | null;
  input_cost: string | null;
  output_cost: string | null;
  ttft_ms: number | null;
  api_key_id: string | null;
  error_type: string | null;
  error_code: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
}

export interface ApplicationResponse {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  environment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreateInput {
  name: string;
  slug: string;
  description?: string | null;
  environment?: string | null;
}

export interface ApplicationUpdateInput {
  name?: string;
  description?: string | null;
  environment?: string | null;
}

export interface SessionResponse {
  authenticated: boolean;
  email: string | null;
}

/** Shared time-range + entity filters accepted by analytics endpoints. */
export interface RangeFilters {
  from?: string;
  to?: string;
  provider?: string;
  model?: string;
  application_id?: string;
  environment?: string;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort?: string;
  order?: "asc" | "desc";
}
