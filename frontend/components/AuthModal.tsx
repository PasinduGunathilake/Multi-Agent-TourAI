"use client";

import React from "react";
import { LoginForm } from "@/components/login-form";

interface AuthModalProps {
  isOpen: boolean;
  onClose?: () => void;
  initialMode?: "signin" | "signup" | "setup";
}

export default function AuthModal({
  isOpen,
  onClose,
  initialMode = "signin",
}: AuthModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-sm md:max-w-4xl"
        onClick={(e) => e.stopPropagation()}
      >
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="absolute top-3 right-3 md:top-4 md:right-4 z-20 w-8 h-8 flex items-center justify-center rounded-full bg-black/50 hover:bg-black/80 border border-white/10 text-white/50 hover:text-white transition-all text-sm font-mono cursor-pointer"
            aria-label="Close"
          >
            ✕
          </button>
        )}
        <LoginForm onSuccess={onClose} initialMode={initialMode} />
      </div>
    </div>
  );
}
