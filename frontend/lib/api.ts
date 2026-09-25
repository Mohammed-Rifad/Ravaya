import { env } from "@/lib/env";
import type { ApiError, ApiErrorBody, HealthResponse } from "@/types/api";

/** Every API call returns either data or the standard error, never throws. */
export type Result<T> = { ok: true; data: T } | { ok: false; error: ApiErrorBody };

const networkError: ApiErrorBody = {
  code: "network_error",
  message: "Could not reach the API.",
  field: null,
};

export async function getHealth(): Promise<Result<HealthResponse>> {
  try {
    const res = await fetch(`${env.apiUrl}/health/`, {
      cache: "no-store", // always live, never a cached answer
      signal: AbortSignal.timeout(5000), // don't hang if the API is down
    });
    const body: unknown = await res.json();
    if (!res.ok) return { ok: false, error: (body as ApiError).error };
    return { ok: true, data: body as HealthResponse };
  } catch {
    return { ok: false, error: networkError };
  }
}
