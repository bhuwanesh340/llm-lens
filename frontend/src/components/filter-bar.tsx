"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import type { RangeFilters } from "@/lib/types";

interface FilterBarProps {
  filters: RangeFilters;
  onChange: (updates: Partial<RangeFilters>) => void;
  onClear: () => void;
}

/** Shared date-range + provider/model/environment filter controls (T059). */
export function FilterBar({ filters, onChange, onClear }: FilterBarProps) {
  return (
    <div className="bg-card flex flex-wrap items-end gap-4 rounded-lg border p-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-from">From</Label>
        <Input
          id="filter-from"
          type="datetime-local"
          value={filters.from ?? ""}
          onChange={(e) => onChange({ from: e.target.value })}
          className="w-56"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-to">To</Label>
        <Input
          id="filter-to"
          type="datetime-local"
          value={filters.to ?? ""}
          onChange={(e) => onChange({ to: e.target.value })}
          className="w-56"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-provider">Provider</Label>
        <Input
          id="filter-provider"
          placeholder="openai"
          value={filters.provider ?? ""}
          onChange={(e) => onChange({ provider: e.target.value })}
          className="w-40"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-model">Model</Label>
        <Input
          id="filter-model"
          placeholder="gpt-4o-mini"
          value={filters.model ?? ""}
          onChange={(e) => onChange({ model: e.target.value })}
          className="w-40"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-environment">Environment</Label>
        <Input
          id="filter-environment"
          placeholder="production"
          value={filters.environment ?? ""}
          onChange={(e) => onChange({ environment: e.target.value })}
          className="w-36"
        />
      </div>
      <Button variant="outline" onClick={onClear}>
        Clear filters
      </Button>
    </div>
  );
}
