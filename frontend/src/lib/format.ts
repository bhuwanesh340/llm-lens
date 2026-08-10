/** Shared display-formatting helpers for the dashboard pages. */

export function formatCost(value: string | null): string {
  if (value === null) return "—";
  const num = Number(value);
  if (Number.isNaN(num)) return "—";
  return num < 0.01 && num > 0
    ? `$${num.toFixed(6)}`
    : num.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function formatNumber(value: number | null): string {
  if (value === null) return "—";
  return value.toLocaleString();
}

export function formatLatency(value: number | null): string {
  if (value === null) return "—";
  return `${Math.round(value)} ms`;
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatDateTime(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}
