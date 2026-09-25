function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(`Missing ${name}. Copy .env.example to frontend/.env.local and set it.`);
  }
  return value;
}

export const env = {
  // Must be written out as process.env.NEXT_PUBLIC_API_URL: Next.js only inlines
  // literal references, not process.env[name] or destructuring.
  apiUrl: required("NEXT_PUBLIC_API_URL", process.env.NEXT_PUBLIC_API_URL).replace(/\/+$/, ""),
} as const;
