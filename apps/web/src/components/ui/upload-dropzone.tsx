"use client";

import * as React from "react";
import { Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  accept?: string;
  multiple?: boolean;
  onFiles: (files: File[]) => void;
  className?: string;
  label?: string;
  maxSizeMB?: number;
}

function UploadDropzone({ accept = "image/*", multiple = false, onFiles, className, label, maxSizeMB = 10 }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const files = Array.from(e.dataTransfer.files).filter((f) => f.size <= maxSizeMB * 1024 * 1024);
    if (files.length) onFiles(files);
  };

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors cursor-pointer",
        dragActive ? "border-zinc-900 bg-zinc-50 dark:border-zinc-400 dark:bg-zinc-800" : "border-zinc-300 hover:border-zinc-400 dark:border-zinc-700",
        className
      )}
      onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <Upload className="h-8 w-8 text-zinc-400 mb-2" />
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{label || `Drop files here or click to upload (max ${maxSizeMB}MB)`}</p>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(e) => {
          const files = Array.from(e.target.files || []).filter((f) => f.size <= maxSizeMB * 1024 * 1024);
          if (files.length) onFiles(files);
        }}
      />
    </div>
  );
}

export { UploadDropzone };