"use client";

import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { projectsApi } from "@/lib/api";
import type { RangeFilters } from "@/lib/types";

interface FilterBarProps {
  filters: RangeFilters;
  onChange: (updates: Partial<RangeFilters>) => void;
  onClear: () => void;
}

const SELECT_CLASS =
  "border-input bg-background focus-visible:ring-ring/50 h-9 w-44 rounded-md border px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-[3px]";

/** Shared date-range + project/provider/model/environment filters (T059, T126). */
export function FilterBar({ filters, onChange, onClear }: FilterBarProps) {
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectsApi.list(),
    staleTime: 60_000,
  });

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
        <Label htmlFor="filter-project">Project</Label>
        <select
          id="filter-project"
          value={filters.project_id ?? ""}
          onChange={(e) => onChange({ project_id: e.target.value })}
          className={SELECT_CLASS}
        >
          <option value="">All projects</option>
          <option value="unassigned">Unassigned</option>
          {projectsQuery.data?.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
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
