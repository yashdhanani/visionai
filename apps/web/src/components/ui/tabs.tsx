"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsContextType {
  activeValue: string;
  onValueChange: (v: string) => void;
}

const TabsContext = React.createContext<TabsContextType>({ activeValue: "", onValueChange: () => {} });

const Tabs = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { value: string; onValueChange: (v: string) => void }>(
  ({ className, value, onValueChange, children, ...props }, ref) => (
    <TabsContext.Provider value={{ activeValue: value, onValueChange }}>
      <div ref={ref} className={cn("", className)} {...props}>{children}</div>
    </TabsContext.Provider>
  )
);
Tabs.displayName = "Tabs";

const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex h-10 items-center rounded-lg bg-zinc-100 p-1 dark:bg-zinc-800", className)} {...props} />
  )
);
TabsList.displayName = "TabsList";

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, ...props }, ref) => {
    const ctx = React.useContext(TabsContext);
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all cursor-pointer",
          ctx.activeValue === value ? "bg-white shadow-sm dark:bg-zinc-950" : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400",
          className
        )}
        onClick={() => ctx.onValueChange(value)}
        {...props}
      />
    );
  }
);
TabsTrigger.displayName = "TabsTrigger";

const TabsContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { value: string }>(
  ({ className, value, ...props }, ref) => {
    const ctx = React.useContext(TabsContext);
    if (value !== ctx.activeValue) return null;
    return <div ref={ref} className={cn("mt-4", className)} {...props} />;
  }
);
TabsContent.displayName = "TabsContent";

export { Tabs, TabsList, TabsTrigger, TabsContent };