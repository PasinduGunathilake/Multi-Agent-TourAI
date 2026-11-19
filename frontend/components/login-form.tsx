"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldSeparator,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react";

export interface LoginFormProps extends React.ComponentProps<"div"> {
  onSuccess?: () => void;
  initialMode?: "signin" | "signup" | "setup";
}

export function LoginForm({
  className,
  onSuccess,
  initialMode = "signin",
  ...props
}: LoginFormProps) {
  const [mode, setMode] = useState<"signin" | "signup" | "setup">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [setupToken, setSetupToken] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    login,
    register,
    initiateGoogleLogin,
    requestPasswordSetup,
    completePasswordSetup,
  } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    const cleanEmail = email.trim();

    if (mode === "setup") {
      if (!setupToken.trim() || !password) {
        setErrorMsg("Please provide your setup token and a new password.");
        return;
      }
      if (password.length < 8) {
        setErrorMsg("Password must be at least 8 characters with letters and numbers.");
        return;
      }
      setIsSubmitting(true);
      try {
        const { error } = await completePasswordSetup(setupToken.trim(), password);
        if (error) {
          setErrorMsg(error);
        } else {
          setSuccessMsg("Password set successfully! Welcome to TourAI.");
          setTimeout(() => onSuccess?.(), 1000);
        }
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    if (!cleanEmail || !password) {
      setErrorMsg("Please enter both email and password.");
      return;
    }

    if (password.length < 8) {
      setErrorMsg("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === "signin") {
        const { error } = await login(cleanEmail, password);
        if (error) {
          if (error.includes("CREDENTIAL_SETUP_REQUIRED")) {
            setErrorMsg(
              "Initial password setup required for this account. Click 'Forgot your password?' below."
            );
          } else {
            setErrorMsg(error);
          }
        } else {
          onSuccess?.();
        }
      } else {
        const { error } = await register(cleanEmail, password, displayName);
        if (error) {
          setErrorMsg(error);
        } else {
          setSuccessMsg("Account created successfully!");
          setTimeout(() => onSuccess?.(), 1000);
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestSetupLink = async () => {
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMsg("Please enter your email address to request a setup token.");
      return;
    }
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const { success, message } = await requestPasswordSetup(cleanEmail);
      if (success) {
        setSuccessMsg(
          message || "Verification token generated. Please enter your setup token and new password."
        );
        setMode("setup");
      } else {
        setErrorMsg(message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0 border border-white/10 bg-[#0a0d14]/95 text-white shadow-2xl backdrop-blur-xl">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form onSubmit={handleSubmit} className="p-6 md:p-8 flex flex-col justify-center">
            <FieldGroup>
              <div className="flex flex-col items-center gap-2 text-center">
                
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  {mode === "signin"
                    ? "Welcome back"
                    : mode === "signup"
                    ? "Create an account"
                    : "Password Setup"}
                </h1>
                <p className="text-balance text-xs text-white/50">
                  {mode === "signin"
                    ? "Login to your TourAI account"
                    : mode === "signup"
                    ? "Start isolated, private travel planning sessions"
                    : "Verify token and create a secure password"}
                </p>
              </div>

              {/* Error and Success Alerts */}
              {errorMsg && (
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="leading-relaxed flex-1">{errorMsg}</div>
                </div>
              )}

              {successMsg && (
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-300 text-xs">
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="leading-relaxed flex-1">{successMsg}</div>
                </div>
              )}

              {/* Display Name Field (Sign Up Mode) */}
              {mode === "signup" && (
                <Field>
                  <FieldLabel htmlFor="display-name">Display Name (Optional)</FieldLabel>
                  <Input
                    id="display-name"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Travel Explorer"
                  />
                </Field>
              )}

              {/* Email Field (Sign In & Sign Up Modes) */}
              {mode !== "setup" && (
                <Field>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="m@example.com"
                    required
                  />
                </Field>
              )}

              {/* Setup Token Field (Setup Mode) */}
              {mode === "setup" && (
                <Field>
                  <FieldLabel htmlFor="setup-token">Setup / Verification Token</FieldLabel>
                  <Input
                    id="setup-token"
                    type="text"
                    value={setupToken}
                    onChange={(e) => setSetupToken(e.target.value)}
                    placeholder="Paste your setup token"
                    required
                  />
                </Field>
              )}

              {/* Password Field */}
              <Field>
                <div className="flex items-center">
                  <FieldLabel htmlFor="password">
                    {mode === "setup" ? "New Password" : "Password"}
                  </FieldLabel>
                  {mode === "signin" && (
                    <button
                      type="button"
                      onClick={handleRequestSetupLink}
                      className="ml-auto text-xs text-teal-400 underline-offset-2 hover:underline cursor-pointer"
                    >
                      Forgot your password?
                    </button>
                  )}
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                />
              </Field>

              {/* Submit Button */}
              <Field>
                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-1" />
                      <span>Processing...</span>
                    </>
                  ) : mode === "signin" ? (
                    "Login"
                  ) : mode === "signup" ? (
                    "Create Account"
                  ) : (
                    "Save Password"
                  )}
                </Button>
              </Field>

              {/* Social Login Separator & Google OAuth */}
              {mode !== "setup" && (
                <>
                  <FieldSeparator className="*:data-[slot=field-separator-content]:bg-card">
                    Or continue with
                  </FieldSeparator>

                  <Field>
                    <Button
                      variant="outline"
                      type="button"
                      onClick={initiateGoogleLogin}
                      className="w-full flex items-center justify-center gap-3 py-2.5"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24">
                        <path
                          fill="#4285F4"
                          d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3.03h3.88c2.27-2.09 3.665-5.17 3.665-9.12z"
                        />
                        <path
                          fill="#34A853"
                          d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.03c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.26v3.13C3.25 21.36 7.31 24 12 24z"
                        />
                        <path
                          fill="#FBBC05"
                          d="M5.28 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.57H1.26C.46 8.16 0 9.97 0 12s.46 3.84 1.26 5.43l4.02-3.14z"
                        />
                        <path
                          fill="#EA4335"
                          d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.64 1.26 6.57l4.02 3.14c.95-2.83 3.6-4.96 6.72-4.96z"
                        />
                      </svg>
                      <span>Login with Google</span>
                    </Button>
                  </Field>
                </>
              )}

              {/* Mode Toggles */}
              <FieldDescription className="text-center pt-2">
                {mode === "signin" ? (
                  <>
                    Don&apos;t have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setMode("signup");
                        setErrorMsg(null);
                        setSuccessMsg(null);
                      }}
                      className="text-teal-400 font-semibold underline-offset-2 hover:underline cursor-pointer"
                    >
                      Sign up
                    </button>
                  </>
                ) : mode === "signup" ? (
                  <>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setMode("signin");
                        setErrorMsg(null);
                        setSuccessMsg(null);
                      }}
                      className="text-teal-400 font-semibold underline-offset-2 hover:underline cursor-pointer"
                    >
                      Sign in
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setMode("signin");
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="text-teal-400 font-semibold underline-offset-2 hover:underline cursor-pointer"
                  >
                    Back to Login
                  </button>
                )}
              </FieldDescription>
            </FieldGroup>
          </form>

          {/* Right-Side Decorative Showcase */}
          <div className="relative hidden bg-muted md:block overflow-hidden rounded-r-2xl border-l border-white/10">
            <img
              src="/placeholder.svg"
              alt="TourAI Travel Experience"
              className="absolute inset-0 h-full w-full object-cover dark:brightness-[0.85]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent flex flex-col justify-end p-8 text-white">
              <span className="text-[10px] font-mono tracking-widest text-teal-400 uppercase mb-1">
                Multi-Agent System
              </span>
              <h3 className="text-lg font-bold text-white mb-1">
                Explore the World with TourAI
              </h3>
              <p className="text-xs text-white/60 leading-relaxed">
                Autonomous itinerary planning, real-time live search, and verified destination intelligence.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <FieldDescription className="px-6 text-center text-[11px] text-white/40">
        By clicking continue, you agree to our{" "}
        <a href="#" className="underline underline-offset-2 hover:text-white/70">
          Terms of Service
        </a>{" "}
        and{" "}
        <a href="#" className="underline underline-offset-2 hover:text-white/70">
          Privacy Policy
        </a>
        .
      </FieldDescription>
    </div>
  );
}

