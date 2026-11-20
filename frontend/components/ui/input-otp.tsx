"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Minus } from "lucide-react";

interface InputOTPContextType {
  value: string;
  maxLength: number;
  focusedIndex: number;
  onChange: (val: string) => void;
  disabled?: boolean;
}

const InputOTPContext = React.createContext<InputOTPContextType | null>(null);

export interface InputOTPProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  maxLength?: number;
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
  "aria-label"?: string;
}

export const InputOTP = React.forwardRef<HTMLDivElement, InputOTPProps>(
  (
    {
      className,
      maxLength = 6,
      value,
      onChange,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const inputRef = React.useRef<HTMLInputElement>(null);
    const [isFocused, setIsFocused] = React.useState(false);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const cleaned = e.target.value.replace(/\D/g, "").slice(0, maxLength);
      onChange(cleaned);
    };

    const handleClick = () => {
      inputRef.current?.focus();
    };

    const focusedIndex = isFocused ? Math.min(value.length, maxLength - 1) : -1;

    return (
      <InputOTPContext.Provider
        value={{ value, maxLength, focusedIndex, onChange, disabled }}
      >
        <div
          ref={ref}
          onClick={handleClick}
          className={cn(
            "relative flex items-center justify-center gap-2 cursor-pointer select-none",
            className
          )}
          {...props}
        >
          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={maxLength}
            value={value}
            disabled={disabled}
            onChange={handleInputChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            aria-label={props["aria-label"] || "Verification code"}
            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
          />
          {children}
        </div>
      </InputOTPContext.Provider>
    );
  }
);
InputOTP.displayName = "InputOTP";

export function InputOTPGroup({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center gap-1.5", className)}
      {...props}
    />
  );
}

export function InputOTPSeparator({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="separator"
      className={cn("flex items-center justify-center text-white/40 px-1", className)}
      {...props}
    >
      <Minus className="w-4 h-4" />
    </div>
  );
}

export interface InputOTPSlotProps extends React.HTMLAttributes<HTMLDivElement> {
  index: number;
}

export function InputOTPSlot({ index, className, ...props }: InputOTPSlotProps) {
  const ctx = React.useContext(InputOTPContext);
  if (!ctx) {
    throw new Error("InputOTPSlot must be used within an InputOTP");
  }

  const char = ctx.value[index] || "";
  const isCurrentActive = ctx.focusedIndex === index;

  return (
    <div
      className={cn(
        "relative flex h-12 w-10 sm:h-12 sm:w-11 items-center justify-center rounded-xl border text-sm font-mono font-semibold transition-all",
        "border-white/10 bg-black/40 text-white",
        isCurrentActive && "border-teal-400 ring-2 ring-teal-400/20 shadow-[0_0_12px_rgba(45,212,191,0.25)]",
        char && "border-white/20 bg-white/[0.04]",
        className
      )}
      {...props}
    >
      {char}
      {isCurrentActive && !char && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="h-5 w-0.5 animate-pulse bg-teal-400 duration-1000" />
        </div>
      )}
    </div>
  );
}
