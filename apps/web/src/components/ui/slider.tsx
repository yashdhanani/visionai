"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  min?: number;
  max?: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
  label?: string;
  suffix?: string;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, min = 0, max = 1, step = 0.01, value, onChange, label, suffix, ...props }, ref) => {
    const pct = ((value - min) / (max - min)) * 100;
    return (
      <div className="space-y-1">
        {label && (
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>{label}</span>
            <span className="font-mono font-medium text-zinc-700 dark:text-zinc-300">
              {value.toFixed(step < 1 ? 2 : 0)}{suffix || ""}
            </span>
          </div>
        )}
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className={cn("w-full h-2 rounded-lg appearance-none cursor-pointer bg-zinc-200 dark:bg-zinc-700 accent-zinc-900 dark:accent-zinc-100", className)}
          {...props}
        />
      </div>
    );
  }
);
Slider.displayName = "Slider";

export { Slider };