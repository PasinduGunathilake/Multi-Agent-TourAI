import { refreshSessionApi, getMemoryToken, setMemoryToken } from "@/lib/auth/auth-api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export interface StreamEvent {
  event?: string;
  thread_id?: string;
  node?: string;
  intent?: string;
  token?: string;
  question?: string;
  draft_itinerary?: string;
  flight_results?: string;
  hotel_results?: string;
  weather_results?: string;
  maps_results?: string;
  itinerary?: string;
  answer?: string;
  llm_calls?: number;
  message?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Performs an authenticated fetch against the FastAPI backend.
 * Automatically attaches Authorization: Bearer <token>.
 * On HTTP 401, refreshes session via HttpOnly cookie and retries once.
 */
export async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {},
  getToken: () => Promise<string | null>,
  allowRetry = true
): Promise<Response> {
  let token = (await getToken()) || getMemoryToken();
  if (!token) {
    try {
      const refreshed = await refreshSessionApi();
      token = refreshed.access_token;
      setMemoryToken(token);
    } catch {
      throw new ApiError("Authentication required. Please sign in.", 401);
    }
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  // Handle Token Expiry / 401 with single safe retry via application refresh cookie
  if (response.status === 401 && allowRetry) {
    try {
      const refreshed = await refreshSessionApi();
      if (refreshed && refreshed.access_token) {
        setMemoryToken(refreshed.access_token);
        return authenticatedFetch(endpoint, options, async () => refreshed.access_token, false);
      }
    } catch (refreshErr) {
      console.warn("Session refresh failed during 401 retry:", refreshErr);
    }
  }

  return response;
}

/**
 * Retrieves the authenticated user's travel threads from GET /api/threads.
 */
export async function fetchUserThreads(
  getToken: () => Promise<string | null>
): Promise<{ threads: Array<{ thread_id: string; title: string; status: string; updated_at: string; created_at: string }> }> {
  const res = await authenticatedFetch("/api/threads", { method: "GET" }, getToken);
  if (!res.ok) {
    throw new ApiError(`Failed to fetch user journeys: ${res.statusText}`, res.status);
  }
  return res.json();
}

/**
 * Retrieves past conversation turns for a thread from GET /api/history/{threadId}.
 */
export async function fetchThreadHistory(
  threadId: string,
  getToken: () => Promise<string | null>
): Promise<{ turns: Record<string, unknown>[]; thread_id: string }> {
  const res = await authenticatedFetch(`/api/history/${threadId}`, { method: "GET" }, getToken);
  if (!res.ok) {
    if (res.status === 404) {
      return { turns: [], thread_id: threadId };
    }
    throw new ApiError(`Failed to fetch thread history: ${res.statusText}`, res.status);
  }
  return res.json();
}

/**
 * Deletes a travel journey session and its checkpoints from DELETE /api/session/{threadId}.
 */
export async function deleteThreadSession(
  threadId: string,
  getToken: () => Promise<string | null>
): Promise<{ status: string; thread_id: string }> {
  const res = await authenticatedFetch(`/api/session/${threadId}`, { method: "DELETE" }, getToken);
  if (!res.ok) {
    throw new ApiError(`Failed to delete session: ${res.statusText}`, res.status);
  }
  return res.json();
}

/**
 * Initiates an authenticated real-time SSE stream for trip planning via POST /api/plan/stream.
 */
export async function streamPlanTrip(
  query: string,
  threadId: string | null,
  onEvent: (event: StreamEvent) => void,
  getToken: () => Promise<string | null>
): Promise<void> {
  const res = await authenticatedFetch(
    "/api/plan/stream",
    {
      method: "POST",
      body: JSON.stringify({ query, thread_id: threadId || undefined }),
    },
    getToken
  );

  if (!res.ok || !res.body) {
    let errorDetail = `Stream request failed: ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {}
    throw new ApiError(errorDetail, res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      try {
        const ev = JSON.parse(trimmed.slice(6));
        onEvent(ev);
      } catch {
        // ignore malformed SSE frames
      }
    }
  }
}

/**
 * Initiates an authenticated real-time SSE stream to resume a paused HITL workflow via POST /api/plan/resume/stream.
 */
export async function streamResumeTrip(
  threadId: string,
  approved: boolean,
  feedback: string,
  onEvent: (event: StreamEvent) => void,
  getToken: () => Promise<string | null>
): Promise<void> {
  const res = await authenticatedFetch(
    "/api/plan/resume/stream",
    {
      method: "POST",
      body: JSON.stringify({ thread_id: threadId, approved, feedback }),
    },
    getToken
  );

  if (!res.ok || !res.body) {
    let errorDetail = `Resume stream failed: ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {}
    throw new ApiError(errorDetail, res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      try {
        const ev = JSON.parse(trimmed.slice(6));
        onEvent(ev);
      } catch {
        // ignore malformed SSE frames
      }
    }
  }
}
