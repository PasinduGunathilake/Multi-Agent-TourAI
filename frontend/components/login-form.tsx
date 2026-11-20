"use client";

import React, { useState, useEffect } from "react";
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
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSeparator,
  InputOTPSlot,
} from "@/components/ui/input-otp";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Eye,
  EyeOff,
  Check,
  X,
  ArrowLeft,
  KeyRound,
  ShieldCheck,
} from "lucide-react";

export type LoginFormMode =
  | "signin"
  | "signup"
  | "setup"
  | "forgot"
  | "reset-request"
  | "verify-otp"
  | "new-password";

export interface LoginFormProps extends React.ComponentProps<"div"> {
  onSuccess?: () => void;
  initialMode?: LoginFormMode;
}

const RESEND_DELAY = 60;

export function LoginForm({
  className,
  onSuccess,
  initialMode = "signin",
  ...props
}: LoginFormProps) {
  const [mode, setMode] = useState<LoginFormMode>(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [setupToken, setSetupToken] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [rememberMe, setRememberMe] = useState(true);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Timestamp-based resend countdown persisted across remounts
  const getRemainingCooldown = (): number => {
    if (typeof window === "undefined") return RESEND_DELAY;
    try {
      const stored = sessionStorage.getItem("tourai_otp_cooldown_target");
      if (stored) {
        const target = parseInt(stored, 10);
        const remaining = Math.ceil((target - Date.now()) / 1000);
        return remaining > 0 ? remaining : 0;
      }
    } catch {}
    return 0;
  };

  const setCooldownTarget = (seconds: number) => {
    try {
      if (typeof window !== "undefined") {
        const target = Date.now() + seconds * 1000;
        sessionStorage.setItem("tourai_otp_cooldown_target", target.toString());
      }
    } catch {}
    setCountdown(seconds);
  };

  const [countdown, setCountdown] = useState<number>(() => getRemainingCooldown());
  const canResend = countdown === 0;

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [emailValidationMsg, setEmailValidationMsg] = useState<string | null>(null);
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTokenExpired, setIsTokenExpired] = useState(false);

  const {
    login,
    register,
    initiateGoogleLogin,
    completePasswordSetup,
    checkEmail,
    forgotPassword,
    verifyResetOtp,
    resetPassword,
    resendResetOtp,
    oauthError,
    clearOAuthError,
  } = useAuth();

  // Active error combines local form errors and Google OAuth callback errors
  const effectiveError = errorMsg || oauthError;

  // Resend cooldown timer for OTP verification step
  useEffect(() => {
    if (mode !== "verify-otp") return;

    const updateTimer = () => {
      const rem = getRemainingCooldown();
      setCountdown(rem);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [mode]);

  // Autofocus first OTP slot on transition to verify-otp
  useEffect(() => {
    if (mode === "verify-otp") {
      const timer = setTimeout(() => {
        const firstSlot = document.querySelector<HTMLInputElement>(
          '[data-slot="input-otp-slot"][tabindex="0"], input[autocomplete="one-time-code"]'
        );
        firstSlot?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [mode]);

  // Real-time password criteria
  const hasMinLength = password.length >= 8;
  const hasLetter = /[A-Za-z]/.test(password);
  const hasNumberOrSymbol = /[\d\W]/.test(password);
  const passwordsMatch = password.length > 0 && password === confirmPassword;
  const isPasswordValid = hasMinLength && hasLetter && hasNumberOrSymbol;

  const validateEmailFormat = (val: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
  };

  // Real-time email validation on blur / tab switch
  const handleEmailBlur = async () => {
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setEmailValidationMsg(null);
      return;
    }

    if (!validateEmailFormat(cleanEmail)) {
      setEmailValidationMsg("Please enter a valid email address.");
      return;
    }

    setIsCheckingEmail(true);
    try {
      const res = await checkEmail(cleanEmail);
      if (mode === "signin") {
        if (!res.exists) {
          setEmailValidationMsg(
            "This email address is not registered. Please check your email or create an account."
          );
        } else {
          setEmailValidationMsg(null);
        }
      } else if (mode === "signup") {
        if (res.exists) {
          setEmailValidationMsg(
            "This email address is already registered. Please sign in instead."
          );
        } else {
          setEmailValidationMsg(null);
        }
      } else if (mode === "forgot" || mode === "reset-request") {
        if (!res.exists) {
          setEmailValidationMsg(
            "This email address is not registered. Please check your email or create an account."
          );
        } else if (res.isOAuth && !res.hasPassword) {
          setEmailValidationMsg(
            "This account was registered with Google Sign-In and does not have a password configured."
          );
        } else {
          setEmailValidationMsg(null);
        }
      }
    } catch {
      // Network issues during blur shouldn't hard-block user typing
    } finally {
      setIsCheckingEmail(false);
    }
  };

  // Pre-validate email before navigating to Forgot Password screen
  const handleForgotPasswordClick = async () => {
    clearOAuthError();
    setEmailValidationMsg(null);
    setErrorMsg(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      const emptyMsg = "Please enter your email address to reset your password.";
      setErrorMsg(emptyMsg);
      setEmailValidationMsg(emptyMsg);
      return;
    }

    if (!validateEmailFormat(cleanEmail)) {
      const invalidMsg = "Please enter a valid email address.";
      setErrorMsg(invalidMsg);
      setEmailValidationMsg(invalidMsg);
      return;
    }

    setIsCheckingEmail(true);
    try {
      const res = await checkEmail(cleanEmail);
      if (!res.exists) {
        const notFoundMsg =
          "This email address is not registered. Please check your email or create an account.";
        setErrorMsg(notFoundMsg);
        setEmailValidationMsg(notFoundMsg);
        return; // Retain user on login page with red error text
      }
      if (res.isOAuth && !res.hasPassword) {
        const oauthMsg =
          "This account was registered with Google Sign-In and does not have a password configured. Please sign in with Google.";
        setErrorMsg(oauthMsg);
        setEmailValidationMsg(oauthMsg);
        return;
      }

      // Valid registered email: navigate to forgot password screen
      setErrorMsg(null);
      setEmailValidationMsg(null);
      setSuccessMsg(null);
      setMode("forgot");
    } finally {
      setIsCheckingEmail(false);
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearOAuthError();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsTokenExpired(false);

    const cleanEmail = email.trim();

    // 1. Forgot Password / Request OTP
    if (mode === "forgot" || mode === "reset-request") {
      if (!cleanEmail) {
        setErrorMsg("Please enter your registered email address.");
        setEmailValidationMsg("Please enter your registered email address.");
        return;
      }
      setIsSubmitting(true);
      try {
        const res = await forgotPassword(cleanEmail);
        if (!res.success) {
          // If given email not in database: show red colour text for validation!
          // Stays on this screen so the user clearly sees the red error and can change the email
          setErrorMsg(res.message);
          setEmailValidationMsg(res.message);
          return;
        }
        // Only navigate to OTP verification after backend confirms OTP generated & email delivery accepted
        setEmailValidationMsg(null);
        setSuccessMsg(res.message);
        setCooldownTarget(RESEND_DELAY);
        setOtp("");
        setMode("verify-otp");
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    // 2. Verify OTP (Step 2)
    if (mode === "verify-otp") {
      if (otp.length !== 6) {
        setErrorMsg("Please enter the complete 6-digit verification code.");
        return;
      }
      setIsSubmitting(true);
      try {
        const { success, resetToken: token, message } = await verifyResetOtp(cleanEmail, otp);
        if (success && token) {
          setResetToken(token);
          setPassword("");
          setConfirmPassword("");
          setSuccessMsg("Code verified! Please create your new password.");
          setMode("new-password");
        } else {
          setErrorMsg(message);
        }
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    // 3. New Password (Step 3)
    if (mode === "new-password") {
      if (!password) {
        setErrorMsg("Please enter a new password.");
        return;
      }
      if (!isPasswordValid) {
        setErrorMsg("Password must be at least 8 characters and include both letters and numbers/symbols.");
        return;
      }
      if (password !== confirmPassword) {
        setErrorMsg("Passwords do not match.");
        return;
      }
      setIsSubmitting(true);
      try {
        const { success, message } = await resetPassword(resetToken, password, confirmPassword);
        if (success) {
          setSuccessMsg(
            "Your password has been reset successfully. Please log in using your new password."
          );
          setPassword("");
          setConfirmPassword("");
          setResetToken("");
          setOtp("");
          setTimeout(() => {
            setMode("signin");
            setSuccessMsg("Your password has been reset. Please enter your new password to log in.");
          }, 1800);
        } else {
          setErrorMsg(message);
          if (message.toLowerCase().includes("expired") || message.toLowerCase().includes("invalid")) {
            setIsTokenExpired(true);
          }
        }
      } finally {
        setIsSubmitting(false);
      }
      return;
    }

    // 4. Initial Password Setup (Legacy/Invite Token)
    if (mode === "setup") {
      if (!setupToken.trim() || !password) {
        setErrorMsg("Please provide your setup token and a new password.");
        return;
      }
      if (!isPasswordValid) {
        setErrorMsg("Password must be at least 8 characters with letters and numbers/symbols.");
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

    // 5. Sign In / Sign Up
    if (!cleanEmail || !password) {
      setErrorMsg("Please enter both email and password.");
      return;
    }

    if (emailValidationMsg) {
      setErrorMsg(emailValidationMsg);
      return;
    }

    if (mode === "signup") {
      if (!isPasswordValid) {
        setErrorMsg("Password must be at least 8 characters and include both letters and numbers/symbols.");
        return;
      }
      if (password !== confirmPassword) {
        setErrorMsg("Passwords do not match.");
        return;
      }
    } else {
      if (password.length < 8) {
        setErrorMsg("Password must be at least 8 characters.");
        return;
      }
    }

    setIsSubmitting(true);
    try {
      if (mode === "signin") {
        const { error } = await login(cleanEmail, password, rememberMe);
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
        // Direct duplicate validation before registration
        const emailCheck = await checkEmail(cleanEmail);
        if (emailCheck.exists) {
          const dupMsg = "This email address is already registered. Please sign in instead.";
          setEmailValidationMsg(dupMsg);
          setErrorMsg(dupMsg);
          return;
        }

        const { error } = await register(cleanEmail, password, displayName.trim());
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

  // Handle Resend OTP in verify-otp screen
  const handleResendOtp = async () => {
    if (!canResend || isSubmitting) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsSubmitting(true);
    try {
      const { success, message } = await resendResetOtp(email.trim());
      if (success) {
        setCooldownTarget(RESEND_DELAY);
        setOtp("");
        setSuccessMsg(message || "A new verification code has been sent to your email.");
      } else {
        if (
          message.toLowerCase().includes("not registered") ||
          message.toLowerCase().includes("google sign-in") ||
          message.toLowerCase().includes("not eligible")
        ) {
          setMode("signin");
        }
        setErrorMsg(message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Safe Google OAuth initiator with inline error feedback
  const handleGoogleLogin = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);
    const { error } = await initiateGoogleLogin();
    if (error) {
      setErrorMsg(error);
    }
  };

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0 border border-white/10 bg-[#0a0d14]/95 text-white shadow-2xl backdrop-blur-xl">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form onSubmit={handleSubmit} className="p-6 md:p-8 flex flex-col justify-center">
            <FieldGroup>
              {/* Header */}
              <div className="flex flex-col items-center gap-2 text-center">
                {mode === "verify-otp" && (
                  <div className="w-10 h-10 rounded-full bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 mb-1">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                )}
                {mode === "new-password" && (
                  <div className="w-10 h-10 rounded-full bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 mb-1">
                    <KeyRound className="w-5 h-5" />
                  </div>
                )}

                <h1 className="text-2xl font-bold tracking-tight text-white">
                  {mode === "signin"
                    ? "Welcome back"
                    : mode === "signup"
                    ? "Create an account"
                    : mode === "forgot" || mode === "reset-request"
                    ? "Reset your password"
                    : mode === "verify-otp"
                    ? "Enter verification code"
                    : mode === "new-password"
                    ? "Create new password"
                    : "Password Setup"}
                </h1>
                <p className="text-balance text-xs text-white/50">
                  {mode === "signin"
                    ? "Login to your TourAI account"
                    : mode === "signup"
                    ? "Start isolated, private travel planning sessions"
                    : mode === "forgot" || mode === "reset-request"
                    ? "Enter your email to receive a 6-digit verification code"
                    : mode === "verify-otp"
                    ? `We sent a 6-digit code to ${email || "your email"}`
                    : mode === "new-password"
                    ? "Create a strong password for your account"
                    : "Verify token and create a secure password"}
                </p>
              </div>

              {/* Error and Success Alerts */}
              {effectiveError && (
                <div className="flex flex-col gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  <div className="flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <div className="leading-relaxed flex-1">{effectiveError}</div>
                  </div>
                  {isTokenExpired && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setMode("forgot");
                        setIsTokenExpired(false);
                        setErrorMsg(null);
                        clearOAuthError();
                      }}
                      className="w-full mt-1 text-xs text-teal-300 border-teal-500/30 hover:bg-teal-500/10"
                    >
                      Request New Verification Code
                    </Button>
                  )}
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
                    maxLength={50}
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Travel Explorer"
                  />
                </Field>
              )}

              {/* Email Field (Sign In, Sign Up, Forgot Password & Reset Request Modes) */}
              {(mode === "signin" || mode === "signup" || mode === "forgot" || mode === "reset-request") && (
                <Field>
                  <FieldLabel htmlFor="email">Email address</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (emailValidationMsg) setEmailValidationMsg(null);
                      if (errorMsg) setErrorMsg(null);
                    }}
                    onBlur={handleEmailBlur}
                    placeholder="m@example.com"
                    required
                    className={
                      emailValidationMsg ||
                      (effectiveError && (mode === "forgot" || mode === "reset-request"))
                        ? "border-rose-500/60 focus-visible:ring-rose-500/30 text-rose-100"
                        : ""
                    }
                  />
                  {isCheckingEmail && (
                    <p className="text-[11px] text-teal-400 font-medium mt-1.5 flex items-center gap-1.5 animate-pulse">
                      <Loader2 className="w-3.5 h-3.5 shrink-0 animate-spin" />
                      <span>Checking email registration...</span>
                    </p>
                  )}
                  {!isCheckingEmail && emailValidationMsg && (
                    <p className="text-[11px] text-rose-400 font-medium mt-1.5 flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{emailValidationMsg}</span>
                    </p>
                  )}
                </Field>
              )}

              {/* Step 2: OTP Verification Screen */}
              {mode === "verify-otp" && (
                <div className="flex flex-col gap-4 py-2">
                  <div className="flex justify-center">
                    <InputOTP
                      aria-label="Verification code"
                      maxLength={6}
                      onChange={(val) => setOtp(val)}
                      value={otp}
                      disabled={isSubmitting}
                    >
                      <InputOTPGroup>
                        <InputOTPSlot index={0} />
                        <InputOTPSlot index={1} />
                        <InputOTPSlot index={2} />
                      </InputOTPGroup>
                      <InputOTPSeparator />
                      <InputOTPGroup>
                        <InputOTPSlot index={3} />
                        <InputOTPSlot index={4} />
                        <InputOTPSlot index={5} />
                      </InputOTPGroup>
                    </InputOTP>
                  </div>

                  <div className="flex items-center justify-between gap-4 text-xs pt-1 px-1">
                    <span className="text-white/40">
                      {canResend
                        ? "Didn't receive the code?"
                        : `Resend code in ${countdown}s`}
                    </span>
                    <Button
                      className="h-auto p-0 text-teal-400 hover:text-teal-300 font-semibold"
                      disabled={!canResend || isSubmitting}
                      onClick={handleResendOtp}
                      size="sm"
                      type="button"
                      variant="link"
                    >
                      Resend Code
                    </Button>
                  </div>
                </div>
              )}

              {/* Password Fields for Registration Mode */}
              {mode === "signup" && (
                <>
                  <Field>
                    <FieldLabel htmlFor="password">Password</FieldLabel>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors cursor-pointer p-1"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? (
                          <EyeOff className="w-4 h-4 text-white/70 hover:text-white" />
                        ) : (
                          <Eye className="w-4 h-4 text-white/70 hover:text-white" />
                        )}
                      </button>
                    </div>
                  </Field>

                  <Field>
                    <FieldLabel htmlFor="confirm-password">Confirm Password</FieldLabel>
                    <div className="relative">
                      <Input
                        id="confirm-password"
                        type={showConfirmPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors cursor-pointer p-1"
                        aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="w-4 h-4 text-white/70 hover:text-white" />
                        ) : (
                          <Eye className="w-4 h-4 text-white/70 hover:text-white" />
                        )}
                      </button>
                    </div>
                  </Field>

                  {/* Password Criteria Feedback for Registration */}
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5 text-[11px]">
                    <div className={cn("flex items-center gap-1.5", hasMinLength ? "text-teal-400" : "text-white/40")}>
                      {hasMinLength ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                      <span>At least 8 characters</span>
                    </div>
                    <div className={cn("flex items-center gap-1.5", hasLetter ? "text-teal-400" : "text-white/40")}>
                      {hasLetter ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                      <span>Contains at least one letter</span>
                    </div>
                    <div className={cn("flex items-center gap-1.5", hasNumberOrSymbol ? "text-teal-400" : "text-white/40")}>
                      {hasNumberOrSymbol ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                      <span>Contains a number or special character</span>
                    </div>
                    {confirmPassword.length > 0 && (
                      <div className={cn("flex items-center gap-1.5", passwordsMatch ? "text-teal-400" : "text-rose-400")}>
                        {passwordsMatch ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                        <span>{passwordsMatch ? "Passwords match" : "Passwords do not match"}</span>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Step 3: New Password Screen */}
              {mode === "new-password" && (
                <>
                  <Field>
                    <FieldLabel htmlFor="new-password">New Password</FieldLabel>
                    <div className="relative">
                      <Input
                        id="new-password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors cursor-pointer p-1"
                        aria-label={showPassword ? "Hide new password" : "Show new password"}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4 text-white/70 hover:text-white" /> : <Eye className="w-4 h-4 text-white/70 hover:text-white" />}
                      </button>
                    </div>
                  </Field>

                  <Field>
                    <FieldLabel htmlFor="confirm-password">Confirm New Password</FieldLabel>
                    <div className="relative">
                      <Input
                        id="confirm-password"
                        type={showConfirmPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors cursor-pointer p-1"
                        aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4 text-white/70 hover:text-white" /> : <Eye className="w-4 h-4 text-white/70 hover:text-white" />}
                      </button>
                    </div>
                  </Field>

                  {/* Password Criteria Feedback */}
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1.5 text-[11px]">
                    <div className={cn("flex items-center gap-1.5", hasMinLength ? "text-teal-400" : "text-white/40")}>
                      {hasMinLength ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                      <span>At least 8 characters</span>
                    </div>
                    <div className={cn("flex items-center gap-1.5", hasLetter ? "text-teal-400" : "text-white/40")}>
                      {hasLetter ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                      <span>Contains at least one letter</span>
                    </div>
                    <div className={cn("flex items-center gap-1.5", hasNumberOrSymbol ? "text-teal-400" : "text-white/40")}>
                      {hasNumberOrSymbol ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                      <span>Contains a number or special character</span>
                    </div>
                    {confirmPassword.length > 0 && (
                      <div className={cn("flex items-center gap-1.5", passwordsMatch ? "text-teal-400" : "text-rose-400")}>
                        {passwordsMatch ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                        <span>{passwordsMatch ? "Passwords match" : "Passwords do not match"}</span>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Password Field for Sign In Mode */}
              {mode === "signin" && (
                <Field>
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors cursor-pointer p-1"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? (
                        <EyeOff className="w-4 h-4 text-white/70 hover:text-white" />
                      ) : (
                        <Eye className="w-4 h-4 text-white/70 hover:text-white" />
                      )}
                    </button>
                  </div>

                  {/* Remember Me & Forgot Password Controls */}
                  <div className="flex items-center justify-between mt-2 pt-0.5">
                    <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-white/60 hover:text-white/80">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="rounded border-white/20 bg-white/5 text-teal-500 focus:ring-teal-500 cursor-pointer"
                      />
                      <span>Remember me</span>
                    </label>
                    <button
                      type="button"
                      onClick={handleForgotPasswordClick}
                      disabled={isCheckingEmail}
                      className="text-xs text-teal-400 hover:text-teal-300 font-medium underline-offset-2 hover:underline cursor-pointer disabled:opacity-50"
                    >
                      {isCheckingEmail ? "Checking..." : "Forgot your password?"}
                    </button>
                  </div>
                </Field>
              )}

              {/* Setup Token Field (Legacy Setup Mode) */}
              {mode === "setup" && (
                <>
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
                  <Field>
                    <FieldLabel htmlFor="password">New Password</FieldLabel>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors cursor-pointer p-1"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? (
                          <EyeOff className="w-4 h-4 text-white/70 hover:text-white" />
                        ) : (
                          <Eye className="w-4 h-4 text-white/70 hover:text-white" />
                        )}
                      </button>
                    </div>
                  </Field>
                </>
              )}

              {/* Primary Action Button */}
              <Field>
                <Button
                  type="submit"
                  disabled={
                    isSubmitting ||
                    (mode === "verify-otp" && otp.length !== 6) ||
                    ((mode === "new-password" || mode === "signup") && (!isPasswordValid || !passwordsMatch))
                  }
                  className="w-full mt-1 text-sm font-semibold text-white bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 border border-teal-400/40 shadow-lg shadow-teal-500/25 cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      <span>Processing...</span>
                    </>
                  ) : mode === "signin" ? (
                    "Login"
                  ) : mode === "signup" ? (
                    "Create Account"
                  ) : mode === "forgot" || mode === "reset-request" ? (
                    "Send Verification Code"
                  ) : mode === "verify-otp" ? (
                    "Verify Code"
                  ) : mode === "new-password" ? (
                    "Reset Password"
                  ) : (
                    "Save Password"
                  )}
                </Button>
              </Field>

              {/* Social Login Separator & Google OAuth (Only on Sign In / Sign Up) */}
              {(mode === "signin" || mode === "signup") && (
                <>
                  <FieldSeparator className="*:data-[slot=field-separator-content]:bg-card">
                    Or continue with
                  </FieldSeparator>

                  <Field>
                    <Button
                      variant="outline"
                      type="button"
                      onClick={handleGoogleLogin}
                      className="w-full text-sm font-medium text-white bg-white/5 hover:bg-white/10 border border-white/20 hover:border-white/30 transition-all flex items-center justify-center gap-3 py-2.5 cursor-pointer"
                    >
                      <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
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
                      <span className="text-white font-medium">Login with Google</span>
                    </Button>
                  </Field>
                </>
              )}

              {/* Mode Toggles & Back Navigation */}
              <FieldDescription className="text-center pt-2">
                {mode === "signin" ? (
                  <>
                    Don&apos;t have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setMode("signup");
                        setEmailValidationMsg(null);
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
                        setEmailValidationMsg(null);
                        setErrorMsg(null);
                        setSuccessMsg(null);
                      }}
                      className="text-teal-400 font-semibold underline-offset-2 hover:underline cursor-pointer"
                    >
                      Sign in
                    </button>
                  </>
                ) : mode === "verify-otp" ? (
                  <button
                    type="button"
                    onClick={() => {
                      setMode("forgot");
                      setEmailValidationMsg(null);
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="inline-flex items-center gap-1.5 text-xs text-white/50 hover:text-white transition-colors cursor-pointer"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Change email address</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setMode("signin");
                      setEmailValidationMsg(null);
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="inline-flex items-center gap-1.5 text-xs text-teal-400 font-semibold underline-offset-2 hover:underline cursor-pointer"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back to Login</span>
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
        <a
          href="#terms"
          onClick={(e) => e.preventDefault()}
          className="underline underline-offset-2 hover:text-white/70"
        >
          Terms of Service
        </a>{" "}
        and{" "}
        <a
          href="#privacy"
          onClick={(e) => e.preventDefault()}
          className="underline underline-offset-2 hover:text-white/70"
        >
          Privacy Policy
        </a>
        .
      </FieldDescription>
    </div>
  );
}
