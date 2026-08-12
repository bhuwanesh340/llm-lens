"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { applicationsApi, ApiError } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ApplicationResponse } from "@/lib/types";

export default function ApplicationsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [environment, setEnvironment] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const applicationsQuery = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      applicationsApi.create({
        name,
        slug,
        description: description || null,
        environment: environment || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Application created");
      setDialogOpen(false);
      setName("");
      setSlug("");
      setDescription("");
      setEnvironment("");
      setFormError(null);
    },
    onError: (err) => {
      setFormError(err instanceof ApiError ? err.message : "Failed to create application");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => applicationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      toast.success("Application deleted");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to delete application");
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Applications</h1>
          <p className="text-muted-foreground">
            Tag requests to applications to filter usage/cost/error views per app.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button>New application</Button>} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create application</DialogTitle>
              <DialogDescription>
                The slug is used as the stable identifier when tagging requests.
              </DialogDescription>
            </DialogHeader>
            <form
              className="flex flex-col gap-4"
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate();
              }}
            >
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="app-name">Name</Label>
                <Input
                  id="app-name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="app-slug">Slug</Label>
                <Input
                  id="app-slug"
                  required
                  pattern="^[a-z0-9][a-z0-9-]*$"
                  placeholder="support-bot"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="app-description">Description</Label>
                <Input
                  id="app-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="app-environment">Environment</Label>
                <Input
                  id="app-environment"
                  placeholder="production"
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                />
              </div>
              {formError ? <p className="text-destructive text-sm">{formError}</p> : null}
              <DialogFooter>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating..." : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All applications</CardTitle>
        </CardHeader>
        <CardContent>
          {applicationsQuery.isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : !applicationsQuery.data || applicationsQuery.data.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center text-sm">
              No applications yet. Create one to start tagging requests.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Slug</TableHead>
                  <TableHead>Environment</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {applicationsQuery.data.map((app: ApplicationResponse) => (
                  <TableRow key={app.id}>
                    <TableCell className="font-medium">{app.name}</TableCell>
                    <TableCell>{app.slug}</TableCell>
                    <TableCell>{app.environment ?? "—"}</TableCell>
                    <TableCell className="max-w-xs truncate">{app.description ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={deleteMutation.isPending}
                        onClick={() => {
                          if (confirm(`Delete application "${app.name}"?`)) {
                            deleteMutation.mutate(app.id);
                          }
                        }}
                      >
                        Delete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
