import { describe, expect, it } from "vitest";
import { formatCost, formatNumber, formatPercent, formatLatency } from "@/lib/format";

describe("formatCost", () => {
  it("formats null as an em dash", () => {
    expect(formatCost(null)).toBe("—");
  });

  it("formats sub-cent costs with extra precision", () => {
    expect(formatCost("0.00010000")).toBe("$0.000100");
  });

  it("formats larger costs as currency", () => {
    expect(formatCost("12.50")).toBe("$12.50");
  });
});

describe("formatNumber", () => {
  it("formats null as an em dash", () => {
    expect(formatNumber(null)).toBe("—");
  });

  it("formats a number with locale grouping", () => {
    expect(formatNumber(1234)).toBe("1,234");
  });
});

describe("formatPercent", () => {
  it("converts a ratio to a percentage string", () => {
    expect(formatPercent(0.5)).toBe("50.0%");
  });
});

describe("formatLatency", () => {
  it("formats null as an em dash", () => {
    expect(formatLatency(null)).toBe("—");
  });

  it("rounds and appends ms", () => {
    expect(formatLatency(123.6)).toBe("124 ms");
  });
});
