"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface DropdownMenuContextValue {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  triggerRef: React.MutableRefObject<HTMLElement | null>;
}

const DropdownMenuContext = React.createContext<DropdownMenuContextValue | null>(
  null
);

export function useDropdownMenu() {
  const context = React.useContext(DropdownMenuContext);
  if (!context) {
    throw new Error("useDropdownMenu must be used within a DropdownMenu");
  }
  return context;
}

export function DropdownMenu({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const [open, setOpen] = React.useState(false);
  const triggerRef = React.useRef<HTMLElement | null>(null);
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      // If click is outside the entire dropdown container, close it
      if (containerRef.current && !containerRef.current.contains(target)) {
        setOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen, triggerRef }}>
      <div
        ref={containerRef}
        className={cn("relative inline-block text-left", className)}
      >
        {children}
      </div>
    </DropdownMenuContext.Provider>
  );
}

export interface DropdownMenuTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  render?: React.ReactElement<any>;
  asChild?: boolean;
}

export const DropdownMenuTrigger = React.forwardRef<
  HTMLButtonElement,
  DropdownMenuTriggerProps
>(({ children, render, asChild, onClick, className, ...props }, ref) => {
  const { open, setOpen, triggerRef } = useDropdownMenu();

  const handleRef = (node: HTMLButtonElement | null) => {
    triggerRef.current = node;
    if (typeof ref === "function") ref(node);
    else if (ref) (ref as any).current = node;
  };

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    onClick?.(e);
    setOpen((prev) => !prev);
  };

  if (render && React.isValidElement(render)) {
    const renderElem = render as React.ReactElement<any>;
    return React.cloneElement(renderElem, {
      ref: handleRef,
      onClick: (e: React.MouseEvent<HTMLButtonElement>) => {
        renderElem.props?.onClick?.(e);
        handleClick(e);
      },
      "aria-expanded": open,
      "data-state": open ? "open" : "closed",
      children: renderElem.props?.children || children,
    } as any);
  }

  if (asChild && React.isValidElement(children)) {
    const childElem = children as React.ReactElement<any>;
    return React.cloneElement(childElem, {
      ref: handleRef,
      onClick: (e: React.MouseEvent<HTMLButtonElement>) => {
        childElem.props?.onClick?.(e);
        handleClick(e);
      },
      "aria-expanded": open,
      "data-state": open ? "open" : "closed",
    } as any);
  }

  return (
    <button
      ref={handleRef}
      type="button"
      onClick={handleClick}
      aria-expanded={open}
      data-state={open ? "open" : "closed"}
      className={cn("inline-flex items-center justify-center cursor-pointer", className)}
      {...props}
    >
      {children}
    </button>
  );
});
DropdownMenuTrigger.displayName = "DropdownMenuTrigger";

export interface DropdownMenuContentProps
  extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "center" | "end";
  side?: "top" | "bottom";
}

export const DropdownMenuContent = React.forwardRef<
  HTMLDivElement,
  DropdownMenuContentProps
>(({ className, align = "end", side = "top", children, ...props }, ref) => {
  const { open } = useDropdownMenu();

  if (!open) return null;

  return (
    <div
      ref={ref}
      className={cn(
        "absolute z-50 overflow-hidden rounded-2xl border border-white/10 bg-[#090d16] p-1.5 text-white shadow-2xl backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-150",
        side === "top" && "bottom-full mb-2 origin-bottom",
        side === "bottom" && "top-full mt-2 origin-top",
        align === "end" && (side === "top" ? "right-0 origin-bottom-right" : "right-0 origin-top-right"),
        align === "start" && (side === "top" ? "left-0 origin-bottom-left" : "left-0 origin-top-left"),
        align === "center" && "left-1/2 -translate-x-1/2",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});
DropdownMenuContent.displayName = "DropdownMenuContent";

export const DropdownMenuGroup = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-1", className)} {...props} />
));
DropdownMenuGroup.displayName = "DropdownMenuGroup";

export const DropdownMenuLabel = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("px-2.5 py-2 text-xs font-semibold text-white/70", className)}
    {...props}
  />
));
DropdownMenuLabel.displayName = "DropdownMenuLabel";

export const DropdownMenuSeparator = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-white/10", className)}
    {...props}
  />
));
DropdownMenuSeparator.displayName = "DropdownMenuSeparator";

export interface DropdownMenuItemProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive";
}

export const DropdownMenuItem = React.forwardRef<
  HTMLButtonElement,
  DropdownMenuItemProps
>(({ className, variant = "default", onClick, children, ...props }, ref) => {
  const { setOpen } = useDropdownMenu();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    onClick?.(e);
    setOpen(false);
  };

  return (
    <button
      ref={ref}
      type="button"
      onClick={handleClick}
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center gap-2.5 rounded-xl px-2.5 py-2 text-xs outline-none transition-colors",
        variant === "default" &&
          "text-white/80 hover:bg-white/10 hover:text-white focus:bg-white/10 focus:text-white",
        variant === "destructive" &&
          "text-rose-400 hover:bg-rose-500/15 hover:text-rose-300 focus:bg-rose-500/15 focus:text-rose-300",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});
DropdownMenuItem.displayName = "DropdownMenuItem";
