import { connection } from "next/server";

import { getHealth } from "@/lib/api";

export default async function Home() {
  await connection(); // run at request time, never at build time
  const health = await getHealth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-4xl font-semibold tracking-wide">RAVAYA</h1>
      <p className="text-neutral-500">Crafted for Your Senses — coming soon.</p>
      {health.ok ? (
        <p role="status" className="text-sm text-green-700">
          API connected
        </p>
      ) : (
        <p role="alert" className="text-sm text-red-700">
          API unavailable: {health.error.message}
        </p>
      )}
    </main>
  );
}
