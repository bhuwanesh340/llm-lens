/**
 * Typed fetch client for the LLM Lens backend API.
 *
 * All requests are sent with `credentials: "include"` so the HTTP-only
 * session cookie set by `POST /api/v1/auth/login` is attached automatically.
 */

import type {
  ApplicationCreateInput,
  ApplicationResponse,
  ApplicationUpdateInput,
  CostBreakdownItem,
  CostTimeseriesItem,
  ErrorBreakdownItem,
  ErrorEnvelope,
  ErrorsSummaryResponse,
  ModelDetailResponse,
  ModelSummaryItem,
  OverviewResponse,
  Page,
  PaginationParams,
  RangeFilters,
  RequestDetail,
  RequestListItem,
  SessionResponse,
  UsageBreakdownItem,
  UsageSummaryResponse,
  UsageTimeseriesItem,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function buildQuery(params?: Record<string, string | number | undefined>): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

function rangeFiltersToParams(filters?: RangeFilters): Record<string, string | undefined> {
  if (!filters) return {};
  return {
    from: filters.from,
    to: filters.to,
    provider: filters.provider,
    model: filters.model,
    application_id: filters.application_id,
    environment: filters.environment,
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const envelope = body as ErrorEnvelope | null;
    throw new ApiError(
      response.status,
      envelope?.error?.code ?? "UNKNOWN_ERROR",
      envelope?.error?.message ?? response.statusText,
    );
  }

  return body as T;
}

// --- Auth -------------------------------------------------------------

export const authApi = {
  login: (email: string, password: string) =>
    request<SessionResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<SessionResponse>("/api/v1/auth/logout", { method: "POST" }),
  session: () => request<SessionResponse>("/api/v1/auth/session"),
};

// --- Overview -----------------------------------------------------------

export const overviewApi = {
  get: (filters?: RangeFilters) =>
    request<OverviewResponse>(`/api/v1/overview${buildQuery(rangeFiltersToParams(filters))}`),
};

// --- Usage ----------------------------------------------------------------

export const usageApi = {
  summary: (filters?: RangeFilters) =>
    request<UsageSummaryResponse>(`/api/v1/usage${buildQuery(rangeFiltersToParams(filters))}`),
  timeseries: (filters?: RangeFilters) =>
    request<UsageTimeseriesItem[]>(
      `/api/v1/usage/timeseries${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byModel: (filters?: RangeFilters) =>
    request<UsageBreakdownItem[]>(
      `/api/v1/usage/by-model${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byProvider: (filters?: RangeFilters) =>
    request<UsageBreakdownItem[]>(
      `/api/v1/usage/by-provider${buildQuery(rangeFiltersToParams(filters))}`,
    ),
};

// --- Costs ------------------------------------------------------------

export const costsApi = {
  timeseries: (filters?: RangeFilters) =>
    request<CostTimeseriesItem[]>(
      `/api/v1/costs/timeseries${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byModel: (filters?: RangeFilters) =>
    request<CostBreakdownItem[]>(
      `/api/v1/costs/by-model${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byProvider: (filters?: RangeFilters) =>
    request<CostBreakdownItem[]>(
      `/api/v1/costs/by-provider${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byApplication: (filters?: RangeFilters) =>
    request<CostBreakdownItem[]>(
      `/api/v1/costs/by-application${buildQuery(rangeFiltersToParams(filters))}`,
    ),
};

// --- Models -------------------------------------------------------------

export const modelsApi = {
  list: (filters?: RangeFilters) =>
    request<ModelSummaryItem[]>(`/api/v1/models${buildQuery(rangeFiltersToParams(filters))}`),
  detail: (modelId: string, filters?: RangeFilters) =>
    request<ModelDetailResponse>(
      `/api/v1/models/${encodeURIComponent(modelId)}${buildQuery(rangeFiltersToParams(filters))}`,
    ),
};

// --- Requests -------------------------------------------------------------

export const requestsApi = {
  list: (filters?: RangeFilters, pagination?: PaginationParams) =>
    request<Page<RequestListItem>>(
      `/api/v1/requests${buildQuery({
        ...rangeFiltersToParams(filters),
        ...pagination,
      })}`,
    ),
  detail: (requestId: string) =>
    request<RequestDetail>(`/api/v1/requests/${encodeURIComponent(requestId)}`),
};

// --- Applications -------------------------------------------------------

export const applicationsApi = {
  list: () => request<ApplicationResponse[]>("/api/v1/applications"),
  get: (id: string) => request<ApplicationResponse>(`/api/v1/applications/${id}`),
  create: (payload: ApplicationCreateInput) =>
    request<ApplicationResponse>("/api/v1/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  update: (id: string, payload: ApplicationUpdateInput) =>
    request<ApplicationResponse>(`/api/v1/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  delete: (id: string) =>
    request<void>(`/api/v1/applications/${id}`, { method: "DELETE" }),
};

// --- Errors -------------------------------------------------------------

export const errorsApi = {
  summary: (filters?: RangeFilters) =>
    request<ErrorsSummaryResponse>(`/api/v1/errors${buildQuery(rangeFiltersToParams(filters))}`),
  byProvider: (filters?: RangeFilters) =>
    request<ErrorBreakdownItem[]>(
      `/api/v1/errors/by-provider${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byModel: (filters?: RangeFilters) =>
    request<ErrorBreakdownItem[]>(
      `/api/v1/errors/by-model${buildQuery(rangeFiltersToParams(filters))}`,
    ),
  byCode: (filters?: RangeFilters) =>
    request<ErrorBreakdownItem[]>(
      `/api/v1/errors/by-code${buildQuery(rangeFiltersToParams(filters))}`,
    ),
};
