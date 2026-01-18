"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type AuditEvent = { ts_ms?: number; agent?: string; event?: string; data?: any; raw?: any };

export default function RunPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("pipeline_payload");
    if (!raw) {
      router.push("/");
      return;
    }
    const payload = JSON.parse(raw);

    let cancelled = false;

    async function run() {
      setIsLoading(true);
      setError(null);
      setAudit([]);
      setDone(false);

      try {
        const res = await fetch("/api/pipeline/run_stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        if (!res.body) throw new Error("No response body (stream unsupported?)");

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          if (cancelled) return;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.trim()) continue;
            const msg = JSON.parse(line);

            if (msg.type === "update") {
              const update = msg.data;
              const maybeAudit = extractAuditFromUpdate(update);
              setAudit((prev) => [...prev, ...(maybeAudit.length ? maybeAudit : [{ raw: update }])]);
            } else if (msg.type === "result") {
              // Store final result for /results page
              sessionStorage.setItem("pipeline_result", JSON.stringify(msg.data));
              setDone(true);
            } else if (msg.type === "error") {
              throw new Error(msg.error || "Unknown streaming error");
            }
          }
        }
      } catch (e: any) {
        setError(e?.message ?? "Unknown error");
      } finally {
        setIsLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [router]);

  function extractAuditFromUpdate(update: any): AuditEvent[] {
    const out: AuditEvent[] = [];
    if (!update || typeof update !== "object") return out;

    for (const nodeName of Object.keys(update)) {
      const patch = update[nodeName];
      if (patch?.audit_log && Array.isArray(patch.audit_log)) {
        for (const entry of patch.audit_log) out.push(entry);
      } else {
        out.push({ agent: nodeName, event: "update", data: patch });
      }
    }
    return out;
  }

  return (
    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl space-y-4">
        <div className="rounded-2xl bg-white/70 p-6">
          <div className="flex items-center justify-between">
            <div className="font-medium">Streaming pipeline</div>
            <div className="text-sm text-gray-600">
              {isLoading ? "Running…" : done ? "Complete" : "Stopped"}
            </div>
          </div>

          {error && <div className="text-red-600 mt-2 text-sm">{error}</div>}

          <div className="mt-4 rounded-xl border border-gray-200 bg-white p-3 max-h-80 overflow-auto">
            <div className="text-xs font-medium mb-2">Audit log (live)</div>
            <ul className="space-y-1 text-xs text-gray-700">
              {audit.slice(-80).map((a, i) => (
                <li key={i}>
                  <span className="text-gray-500">{a.ts_ms ?? ""}</span>{" "}
                  <span className="font-mono">{a.agent ?? "?"}</span>{" "}
                  <span>{a.event ?? "update"}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              className="px-5 py-2 rounded-full bg-black text-white text-sm disabled:opacity-50"
              disabled={!done}
              onClick={() => router.push("/notepad/results")}
            >
              View questions →
            </button>

            <button
              className="px-5 py-2 rounded-full border text-sm"
              onClick={() => router.push("/")}
            >
              Start over
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
