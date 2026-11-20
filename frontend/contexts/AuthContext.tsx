"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import { User, AuthContextType } from "@/lib/auth/auth-types";
import {
  loginApi,
  registerApi,
  refreshSessionApi,
  logoutApi,
  getGoogleAuthUrlApi,
  requestPasswordSetupApi,
  completePasswordSetupApi,
  forgotPasswordApi,
  verifyResetOtpApi,
  resetPasswordApi,
  resendResetOtpApi,
  getMemoryToken,
  setMemoryToken,
  subscribeToken,
  AuthApiError,
} from "@/lib/auth/auth-api";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => getMemoryToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [oauthError, setOauthError] = useState<string | null>(null);

  const clearOAuthError = useCallback(() => {
    setOauthError(null);
  }, []);

  // Broadcast non-sensitive auth state events across tabs (zero tokens transmitted)
  const broadcastAuthEvent = useCallback((type: "LOGIN" | "LOGOUT") => {
    try {
      if (typeof window !== "undefined" && "BroadcastChannel" in window) {
        const channel = new BroadcastChannel("tourai_auth_sync");
        channel.postMessage({ type });
        channel.close();
      }
    } catch {
      // BroadcastChannel optional/restricted in sandboxed contexts
    }
  }, []);

  // Synchronize state whenever memory token is updated externally
  useEffect(() => {
    return subscribeToken((newToken) => {
      setToken(newToken);
    });
  }, []);

  // Multi-tab session synchronization listener
  useEffect(() => {
    if (typeof window === "undefined") return;

    let channel: BroadcastChannel | null = null;
    try {
      if ("BroadcastChannel" in window) {
        channel = new BroadcastChannel("tourai_auth_sync");
        channel.onmessage = async (event) => {
          if (event.data?.type === "LOGOUT") {
            setMemoryToken(null);
            setToken(null);
            setUser(null);
          } else if (event.data?.type === "LOGIN") {
            // Another tab authenticated; safely synchronize via HttpOnly cookie
            try {
              const res = await refreshSessionApi();
              setMemoryToken(res.access_token);
              setToken(res.access_token);
              setUser(res.user);
            } catch {
              // Ignore background sync errors
            }
          }
        };
      }
    } catch {
      // Ignored
    }

    return () => {
      channel?.close();
    };
  }, []);

  // Retrieve current in-memory token, attempting refresh via HttpOnly cookie if absent
  const getToken = useCallback(async (): Promise<string | null> => {
    const activeToken = getMemoryToken() || token;
    if (activeToken) {
      return activeToken;
    }
    try {
      const res = await refreshSessionApi();
      setMemoryToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.access_token;
    } catch {
      setMemoryToken(null);
      setToken(null);
      setUser(null);
      return null;
    }
  }, [token]);

  // Initial session restoration on mount
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      // Check for Google OAuth query parameters
      if (typeof window !== "undefined") {
        const urlParams = new URLSearchParams(window.location.search);
        const authSuccess = urlParams.get("auth_success");
        const authError = urlParams.get("auth_error");

        if (authError) {
          const safeMessage = decodeURIComponent(authError.replace(/\+/g, " "));
          setOauthError(safeMessage || "Google sign-in could not be completed.");
          // Clean URL parameter without reloading
          window.history.replaceState({}, document.title, window.location.pathname);
        } else if (authSuccess) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      }

      try {
        const res = await refreshSessionApi();
        if (isMounted) {
          setMemoryToken(res.access_token);
          setToken(res.access_token);
          setUser(res.user);
        }
      } catch {
        if (isMounted) {
          setMemoryToken(null);
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (
    email: string,
    password: string,
    rememberMe: boolean = true
  ): Promise<{ error: string | null }> => {
    try {
      const res = await loginApi(email, password, rememberMe);
      setMemoryToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      broadcastAuthEvent("LOGIN");
      return { error: null };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Failed to sign in.";
      return { error: msg };
    }
  };

  const register = async (
    email: string,
    password: string,
    displayName?: string
  ): Promise<{ error: string | null }> => {
    try {
      const res = await registerApi(email, password, displayName);
      setMemoryToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      broadcastAuthEvent("LOGIN");
      return { error: null };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Registration failed.";
      return { error: msg };
    }
  };

  const logout = async (): Promise<void> => {
    setMemoryToken(null);
    setToken(null);
    setUser(null);
    broadcastAuthEvent("LOGOUT");
    await logoutApi();
  };

  const initiateGoogleLogin = async (): Promise<{ error: string | null }> => {
    try {
      const { auth_url } = await getGoogleAuthUrlApi();
      if (auth_url && typeof window !== "undefined") {
        window.location.href = auth_url;
        return { error: null };
      }
      return { error: "Google OAuth is not configured or unavailable." };
    } catch (err: unknown) {
      const msg =
        err instanceof AuthApiError
          ? err.message
          : "Google OAuth is not configured or unavailable.";
      return { error: msg };
    }
  };

  const requestPasswordSetup = async (
    email: string
  ): Promise<{ success: boolean; message: string }> => {
    try {
      const res = await requestPasswordSetupApi(email);
      return { success: true, message: res.message };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Failed to request password setup.";
      return { success: false, message: msg };
    }
  };

  const completePasswordSetup = async (
    tokenStr: string,
    newPassword: string
  ): Promise<{ error: string | null }> => {
    try {
      const res = await completePasswordSetupApi(tokenStr, newPassword);
      setMemoryToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return { error: null };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Failed to complete password setup.";
      return { error: msg };
    }
  };

  const forgotPassword = async (
    email: string
  ): Promise<{ success: boolean; message: string }> => {
    try {
      const res = await forgotPasswordApi(email);
      return { success: true, message: res.message };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Failed to request password reset code.";
      return { success: false, message: msg };
    }
  };

  const verifyResetOtp = async (
    email: string,
    otp: string
  ): Promise<{ success: boolean; resetToken?: string; message: string }> => {
    try {
      const res = await verifyResetOtpApi(email, otp);
      return { success: true, resetToken: res.reset_token, message: res.message };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Invalid or expired verification code.";
      return { success: false, message: msg };
    }
  };

  const resetPassword = async (
    resetToken: string,
    newPassword: string,
    confirmPassword?: string
  ): Promise<{ success: boolean; message: string }> => {
    try {
      const res = await resetPasswordApi(resetToken, newPassword, confirmPassword);
      return { success: true, message: res.message };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Failed to reset password.";
      return { success: false, message: msg };
    }
  };

  const resendResetOtp = async (
    email: string
  ): Promise<{ success: boolean; message: string }> => {
    try {
      const res = await resendResetOtpApi(email);
      return { success: true, message: res.message };
    } catch (err: unknown) {
      const msg = err instanceof AuthApiError ? err.message : "Failed to resend verification code.";
      return { success: false, message: msg };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        oauthError,
        clearOAuthError,
        login,
        register,
        logout,
        getToken,
        initiateGoogleLogin,
        requestPasswordSetup,
        completePasswordSetup,
        forgotPassword,
        verifyResetOtp,
        resetPassword,
        resendResetOtp,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
