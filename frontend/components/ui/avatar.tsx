"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type ImageLoadingStatus = "idle" | "loading" | "loaded" | "error";

interface AvatarContextValue {
  status: ImageLoadingStatus;
  setStatus: React.Dispatch<React.SetStateAction<ImageLoadingStatus>>;
}

const AvatarContext = React.createContext<AvatarContextValue | null>(null);

function useAvatarContext() {
  return React.useContext(AvatarContext);
}

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "default" | "sm" | "lg" | "xl";
}

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, size = "default", children, ...props }, ref) => {
    const [status, setStatus] = React.useState<ImageLoadingStatus>("idle");

    return (
      <AvatarContext.Provider value={{ status, setStatus }}>
        <div
          ref={ref}
          className={cn(
            "relative inline-flex shrink-0 select-none items-center justify-center rounded-full bg-teal-900/30 border border-teal-500/20",
            size === "sm" && "h-8 w-8",
            size === "default" && "h-9 w-9",
            size === "lg" && "h-11 w-11",
            size === "xl" && "h-12 w-12",
            className
          )}
          {...props}
        >
          {children}
        </div>
      </AvatarContext.Provider>
    );
  }
);
Avatar.displayName = "Avatar";

export interface AvatarImageProps
  extends React.ImgHTMLAttributes<HTMLImageElement> {}

export const AvatarImage = React.forwardRef<
  HTMLImageElement,
  AvatarImageProps
>(({ className, src, alt = "", onLoad, onError, ...props }, ref) => {
  const context = useAvatarContext();
  const imgRef = React.useRef<HTMLImageElement>(null);

  React.useEffect(() => {
    if (!src) {
      context?.setStatus("error");
    } else {
      context?.setStatus("loading");
    }
  }, [src]);

  // Handle cached image already complete on mount
  React.useEffect(() => {
    if (imgRef.current && imgRef.current.complete && imgRef.current.naturalWidth > 0) {
      context?.setStatus("loaded");
    }
  }, [src]);

  return (
    <img
      ref={(node) => {
        (imgRef as any).current = node;
        if (typeof ref === "function") ref(node);
        else if (ref) (ref as any).current = node;
      }}
      src={src}
      alt={alt}
      onLoad={(e) => {
        context?.setStatus("loaded");
        onLoad?.(e);
      }}
      onError={(e) => {
        context?.setStatus("error");
        onError?.(e);
      }}
      className={cn(
        "aspect-square h-full w-full rounded-full object-cover",
        context?.status !== "loaded" && "hidden",
        className
      )}
      {...props}
    />
  );
});
AvatarImage.displayName = "AvatarImage";

export interface AvatarFallbackProps
  extends React.HTMLAttributes<HTMLDivElement> {}

export const AvatarFallback = React.forwardRef<
  HTMLDivElement,
  AvatarFallbackProps
>(({ className, children, ...props }, ref) => {
  const context = useAvatarContext();

  // Hide fallback as soon as the image successfully loads
  if (context?.status === "loaded") {
    return null;
  }

  return (
    <div
      ref={ref}
      className={cn(
        "flex h-full w-full items-center justify-center rounded-full bg-teal-500/20 text-teal-300 font-bold text-xs select-none",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});
AvatarFallback.displayName = "AvatarFallback";

export interface AvatarBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {}

export const AvatarBadge = React.forwardRef<
  HTMLSpanElement,
  AvatarBadgeProps
>(({ className, ...props }, ref) => {
  return (
    <span
      ref={ref}
      className={cn(
        "absolute bottom-0 right-0 z-20 block h-2.5 w-2.5 rounded-full ring-2 ring-[#07090f] bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] pointer-events-none",
        className
      )}
      {...props}
    />
  );
});
AvatarBadge.displayName = "AvatarBadge";
