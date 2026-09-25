"use client"; // error boundaries must be client components

import { useEffect } from "react";

export default function Error({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error); // Sentry will capture this from Day 3
  }, [error]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-xl font-semibold">Something went wrong</h1>
      <button type="button" onClick={() => retry()} className="rounded border px-4 py-2">
        Try again
      </button>
    </main>
  );
}
