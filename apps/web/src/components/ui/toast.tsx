"use client";

import { useEffect } from "react";
import { Toaster } from "sonner";
import { toast } from "sonner";

function useToast() {
  return {
    success: (msg: string) => toast.success(msg),
    error: (msg: string) => toast.error(msg),
    info: (msg: string) => toast.info(msg),
    warning: (msg: string) => toast.warning(msg),
    dismiss: (id?: string | number) => toast.dismiss(id),
  };
}

function ToastProvider() {
  return <Toaster position="top-right" richColors closeButton />;
}

export { useToast, ToastProvider };