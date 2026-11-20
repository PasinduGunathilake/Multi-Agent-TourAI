import {
  AuthResponse,
  User,
  GenericMessageResponse,
  VerifyOtpResponse,
} from "./auth-types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

// In-memory token storage (synchronously accessible across modules without React lifecycle delays)
let _currentAccessToken: string | null = null;
type TokenListener = (token: string | null) => void;
const _tokenListeners = new Set<TokenListener>();

export function getMemoryToken(): string | null {
  return _currentAccessToken;
}

export function setMemoryToken(token: string | null): void {
  _currentAccessToken = token;
  _tokenListeners.forEach((fn) => {
    try {
      fn(token);
    } catch (e) {
      console.warn("Token listener error:", e);
    }
  });
}

export function subscribeToken(listener: TokenListener): () => void {
  _tokenListeners.add(listener);
  return () => {
    _tokenListeners.delete(listener);
  };
}

// In-flight refresh promise deduplication mutex
let _inFlightRefreshPromise: Promise<AuthResponse> | null = null;

export class AuthApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "AuthApiError";
    this.status = status;
    this.data = data;
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  let json: unknown = null;
  try {
    json = await res.json();
  } catch {
    // response had no json body
  }

  if (!res.ok) {
    const errorMsg =
      (json as { detail?: string })?.detail ||
      (json as { message?: string })?.message ||
      `Request failed with status ${res.status}`;
    throw new AuthApiError(errorMsg, res.status, json);
  }

  return json as T;
}

export async function registerApi(
  email: string,
  password: string,
  displayName?: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include", // Delivers and receives HttpOnly cookies
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
      display_name: displayName?.trim() || undefined,
    }),
  });
  const data = await parseResponse<AuthResponse>(res);
  setMemoryToken(data.access_token);
  return data;
}

export async function loginApi(
  email: string,
  password: string,
  rememberMe: boolean = true
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
      remember_me: rememberMe,
    }),
  });
  const data = await parseResponse<AuthResponse>(res);
  setMemoryToken(data.access_token);
  return data;
}

export async function requestPasswordSetupApi(email: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/auth/request-password-setup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email: email.trim().toLowerCase() }),
  });
  return parseResponse<{ message: string }>(res);
}

export async function completePasswordSetupApi(
  token: string,
  newPassword: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/complete-password-setup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ token: token.trim(), new_password: newPassword }),
  });
  const data = await parseResponse<AuthResponse>(res);
  setMemoryToken(data.access_token);
  return data;
}

export async function forgotPasswordApi(
  email: string
): Promise<GenericMessageResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email: email.trim().toLowerCase() }),
  });
  return parseResponse<GenericMessageResponse>(res);
}

export async function verifyResetOtpApi(
  email: string,
  otp: string
): Promise<VerifyOtpResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/verify-reset-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email: email.trim().toLowerCase(), otp: otp.trim() }),
  });
  return parseResponse<VerifyOtpResponse>(res);
}

export async function resetPasswordApi(
  resetToken: string,
  newPassword: string,
  confirmPassword?: string
): Promise<GenericMessageResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      reset_token: resetToken.trim(),
      new_password: newPassword,
      confirm_password: confirmPassword || undefined,
    }),
  });
  return parseResponse<GenericMessageResponse>(res);
}

export async function resendResetOtpApi(
  email: string
): Promise<GenericMessageResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/resend-reset-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email: email.trim().toLowerCase() }),
  });
  return parseResponse<GenericMessageResponse>(res);
}

export async function getGoogleAuthUrlApi(): Promise<{ auth_url: string; state: string }> {
  const res = await fetch(`${API_BASE_URL}/api/auth/google`, {
    method: "GET",
    credentials: "include",
  });
  return parseResponse<{ auth_url: string; state: string }>(res);
}

export async function getMeApi(token: string): Promise<{ user: User }> {
  const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
    credentials: "include",
  });
  return parseResponse<{ user: User }>(res);
}

export async function refreshSessionApi(): Promise<AuthResponse> {
  // If a refresh is already in-flight, return the same promise to prevent race conditions & token reuse wipeouts
  if (_inFlightRefreshPromise) {
    return _inFlightRefreshPromise;
  }

  _inFlightRefreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      const data = await parseResponse<AuthResponse>(res);
      setMemoryToken(data.access_token);
      return data;
    } catch (err) {
      if (!(err instanceof AuthApiError && err.status === 409 && _currentAccessToken)) {
        setMemoryToken(null);
      }
      throw err;
    } finally {
      _inFlightRefreshPromise = null;
    }
  })();

  return _inFlightRefreshPromise;
}

export async function logoutApi(): Promise<void> {
  setMemoryToken(null);
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch (err) {
    console.warn("Logout error:", err);
  }
}
