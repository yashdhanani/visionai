"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { FolderOpen, Plus, Trash2, Edit } from "lucide-react";
import Link from "next/link";

export default function ProjectsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get("/api/v1/projects").then((r) => r.data.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) => api.post("/api/v1/projects", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowCreate(false);
      setName("");
      setDesc("");
      success("Project created");
    },
    onError: (err: any) => toastError(err.response?.data?.error?.message || "Failed"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/projects/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      success("Project deleted");
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-sm text-zinc-500 mt-1">Organize detections into projects</p>
        </div>
        <Button onClick={() => setShowCreate(true)}><Plus className="h-4 w-4 mr-1" /> New Project</Button>
      </div>

      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : !data?.items?.length ? (
        <Card>
          <CardContent className="p-12 text-center text-zinc-500">
            <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm mb-4">No projects yet. Create your first project to start organizing detections.</p>
            <Button onClick={() => setShowCreate(true)}><Plus className="h-4 w-4 mr-1" /> Create Project</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((proj: any) => (
            <Card key={proj.id} className="hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">{proj.name}</CardTitle>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => { if (confirm("Delete?")) deleteMutation.mutate(proj.id); }}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-zinc-500 mb-3 line-clamp-2">{proj.description || "No description"}</p>
                <p className="text-xs text-zinc-400">Created {new Date(proj.created_at).toLocaleDateString()}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogTitle>Create Project</DialogTitle>
          <div className="space-y-4 mt-4">
            <Input placeholder="Project name" value={name} onChange={(e) => setName(e.target.value)} />
            <Input placeholder="Description (optional)" value={desc} onChange={(e) => setDesc(e.target.value)} />
            <Button className="w-full" disabled={!name.trim()} loading={createMutation.isPending} onClick={() => createMutation.mutate({ name: name.trim(), description: desc.trim() || undefined })}>
              Create
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}