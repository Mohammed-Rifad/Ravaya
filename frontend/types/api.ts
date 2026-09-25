/** The error envelope every API error uses (backend: apps/core/exceptions.py). */
export type ApiErrorBody = {
  code: string;
  message: string;
  field: string | null;
  details?: Record<string, unknown>;
};

export type ApiError = { error: ApiErrorBody };

export type HealthResponse = { status: "ok" };
