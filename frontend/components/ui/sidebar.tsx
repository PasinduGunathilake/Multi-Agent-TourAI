"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
} from "react";
import { PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Types ───────────────────────────────────────────────────────────────────
interface SidebarContextValue {
  state: "expanded" | "collapsed";
  open: boolean;
  setOpen: (open: boolean) => void;
  isMobile: boolean;
  toggleSidebar: () => void;
}

const SidebarContext = createContext<SidebarContextValue | null>(null);

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}

// ── Provider ────────────────────────────────────────────────────────────────
interface SidebarProviderProps {
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}

export function SidebarProvider({
  defaultOpen = false,
  open: controlledOpen,
  onOpenChange,
  className,
  style,
  children,
}: SidebarProviderProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen);
  const [isMobile, setIsMobile] = useState(false);

  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : uncontrolledOpen;

  const setOpen = useCallback(
    (value: boolean) => {
      if (!isControlled) {
        setUncontrolledOpen(value);
      }
      onOpenChange?.(value);
    },
    [isControlled, onOpenChange]
  );

  const toggleSidebar = useCallback(() => {
    setOpen(!open);
  }, [open, setOpen]);

  // Window resize listener
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Keyboard shortcut Ctrl+B / Cmd+B
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleSidebar]);

  const state = open ? "expanded" : "collapsed";

  const value = useMemo(
    () => ({
      state: state as "expanded" | "collapsed",
      open,
      setOpen,
      isMobile,
      toggleSidebar,
    }),
    [state, open, setOpen, isMobile, toggleSidebar]
  );

  return (
    <SidebarContext.Provider value={value}>
      <div
        data-state={state}
        data-collapsible={open ? "" : "icon"}
        className={cn("group/sidebar-wrapper min-h-screen w-full flex", className)}
        style={style}
      >
        {children}
      </div>
    </SidebarContext.Provider>
  );
}

// ── Main Sidebar Shell ──────────────────────────────────────────────────────
interface SidebarProps extends React.HTMLAttributes<HTMLElement> {
  collapsible?: "offcanvas" | "icon" | "none";
  side?: "left" | "right";
  variant?: "sidebar" | "floating" | "inset";
}

export function Sidebar({
  collapsible = "icon",
  className,
  children,
  ...props
}: SidebarProps) {
  const { open } = useSidebar();

  return (
    <aside
      data-state={open ? "expanded" : "collapsed"}
      data-collapsible={collapsible}
      className={cn(
        "fixed top-0 left-0 bottom-0 z-50 h-screen transition-all duration-300 ease-in-out flex flex-col justify-between overflow-hidden",
        "bg-[#080b12] border-r border-white/[0.08] backdrop-blur-xl",
        open ? "w-64" : "w-16",
        className
      )}
      {...props}
    >
      {children}
    </aside>
  );
}

// ── Header ──────────────────────────────────────────────────────────────────
export function SidebarHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col p-3 border-b border-white/[0.06] shrink-0", className)}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Content (Scrollable) ────────────────────────────────────────────────────
export function SidebarContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex-1 overflow-y-auto overflow-x-hidden p-2 space-y-4 custom-scrollbar",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Footer ──────────────────────────────────────────────────────────────────
export function SidebarFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-col p-3 border-t border-white/[0.06] shrink-0 space-y-2",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Group ───────────────────────────────────────────────────────────────────
export function SidebarGroup({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("space-y-1.5", className)} {...props}>
      {children}
    </div>
  );
}

export function SidebarGroupLabel({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  const { open } = useSidebar();
  if (!open) return null;

  return (
    <div
      className={cn(
        "px-2.5 py-1 text-[10px] font-mono font-medium text-white/35 uppercase tracking-wider flex items-center justify-between",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function SidebarGroupAction({
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open } = useSidebar();
  if (!open) return null;

  return (
    <button
      type="button"
      className={cn(
        "text-white/40 hover:text-white transition-colors cursor-pointer p-0.5 rounded",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function SidebarGroupContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("space-y-0.5", className)} {...props}>
      {children}
    </div>
  );
}

// ── Menu ────────────────────────────────────────────────────────────────────
export function SidebarMenu({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLUListElement>) {
  return (
    <ul className={cn("space-y-1 list-none p-0 m-0", className)} {...props}>
      {children}
    </ul>
  );
}

export function SidebarMenuItem({
  className,
  children,
  ...props
}: React.LiHTMLAttributes<HTMLLIElement>) {
  return (
    <li className={cn("relative group/menu-item", className)} {...props}>
      {children}
    </li>
  );
}

// ── Menu Button ─────────────────────────────────────────────────────────────
interface SidebarMenuButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isActive?: boolean;
  tooltip?: string;
  asChild?: boolean;
}

export function SidebarMenuButton({
  isActive,
  tooltip,
  className,
  children,
  ...props
}: SidebarMenuButtonProps) {
  const { open } = useSidebar();

  return (
    <button
      type="button"
      data-active={isActive}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer relative",
        isActive
          ? "bg-teal-500/15 border border-teal-500/30 text-teal-300 shadow-sm shadow-teal-500/10"
          : "text-white/50 hover:text-white hover:bg-white/[0.06] border border-transparent",
        !open && "justify-center px-2",
        className
      )}
      {...props}
    >
      {children}
      {!open && tooltip && (
        <span className="absolute left-16 px-2.5 py-1 rounded-md bg-black/90 border border-white/10 text-[11px] text-white whitespace-nowrap opacity-0 pointer-events-none group-hover/menu-item:opacity-100 transition-opacity z-50 shadow-xl">
          {tooltip}
        </span>
      )}
    </button>
  );
}

// ── Menu Action (e.g. Delete, More) ─────────────────────────────────────────
export function SidebarMenuAction({
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open } = useSidebar();
  if (!open) return null;

  return (
    <button
      type="button"
      className={cn(
        "absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md opacity-0 group-hover/menu-item:opacity-100 text-white/40 hover:text-red-400 hover:bg-white/10 transition-all cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

// ── Menu Badge ──────────────────────────────────────────────────────────────
export function SidebarMenuBadge({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  const { open } = useSidebar();
  if (!open) return null;

  return (
    <span
      className={cn(
        "ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-white/10 text-white/60",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

// ── Trigger Button ──────────────────────────────────────────────────────────
export function SidebarTrigger({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { toggleSidebar } = useSidebar();

  return (
    <button
      type="button"
      onClick={toggleSidebar}
      className={cn(
        "p-2 rounded-xl text-white/50 hover:text-white hover:bg-white/10 border border-white/10 transition-all cursor-pointer",
        className
      )}
      title="Toggle Sidebar (Ctrl+B)"
      {...props}
    >
      <PanelLeft className="w-4 h-4" />
      <span className="sr-only">Toggle Sidebar</span>
    </button>
  );
}

// ── Sidebar Rail (Hoverable Edge Strip) ──────────────────────────────────────
export function SidebarRail() {
  const { toggleSidebar } = useSidebar();

  return (
    <button
      type="button"
      onClick={toggleSidebar}
      className="absolute top-0 right-0 bottom-0 w-1.5 hover:w-2 hover:bg-teal-400/40 transition-all cursor-ew-resize z-50 group"
      title="Toggle Sidebar"
    >
      <span className="sr-only">Toggle Sidebar Rail</span>
    </button>
  );
}

// ── Inset Layout Wrapper ────────────────────────────────────────────────────
export function SidebarInset({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  const { open } = useSidebar();

  return (
    <div
      className={cn(
        "flex-1 flex flex-col min-h-screen transition-all duration-300 ease-in-out relative overflow-x-hidden",
        open ? "pl-64" : "pl-16",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
