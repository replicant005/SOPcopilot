"use client";
import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type AuditEvent = { ts_ms?: number; agent?: string; event?: string; data?: any; raw?: any };
type PiiSpan = { start?: number; end?: number; pii_type?: string; confidence?: number };

export default function RunPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [piiSpans, setPiiSpans] = useState<PiiSpan[]>([]);

  const currentStage = useMemo(() => {
    const last = audit[audit.length - 1];
    if (!last?.agent && !last?.event) return null;
    return `${last.agent ?? "?"} — ${last.event ?? "update"}`;
  }, [audit]);

  useEffect(() => {
    const raw = sessionStorage.getItem("pipeline_payload");
    if (!raw) {
      router.push("/notepad"); // keep consistent with your flow
      return;
    }
    const payload = JSON.parse(raw);

    let cancelled = false;

    async function run() {
      setIsLoading(true);
      setError(null);
      setAudit([]);
      setDone(false);
      setPiiSpans([]);

      try {
        const res = await fetch("/api/pipeline/run_stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        // IMPORTANT: when backend returns validation error, it may still be NDJSON text
        // (status 400). We parse the first JSON line if possible.
        if (!res.ok) {
          const txt = await res.text();
          const firstLine = txt.split("\n").find((l) => l.trim());

          try {
            const j = firstLine ? JSON.parse(firstLine) : null;
            if (j?.type === "error" && j?.error === "INPUT_VALIDATION") {
              // Send back to input page with custom messages
              sessionStorage.setItem("pipeline_validation", JSON.stringify(j.data || {}));
              router.push("/notepad");
              return;
            }
          } catch {
            // fallthrough
          }

          throw new Error(`HTTP ${res.status}: ${txt}`);
        }

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

              // PII spans
              const spans = extractPiiFromUpdate(update);
              if (spans) setPiiSpans(spans);

              // Audit events
            //   const maybeAudit = extractAuditFromUpdate(update);
              const events = extractAuditFromMsgData(msg.data);
              if (events.length) setAudit((prev) => [...prev, ...events]);
            } else if (msg.type === "result") {
              sessionStorage.setItem("pipeline_result", JSON.stringify(msg.data));
              setDone(true);
            } else if (msg.type === "error") {
              // Stream-time error events from backend
              if (msg.error === "INPUT_VALIDATION") {
                sessionStorage.setItem("pipeline_validation", JSON.stringify(msg.data || {}));
                router.push("/notepad");
                return;
              }
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

  function extractPiiFromUpdate(update: any): PiiSpan[] | null {
    if (!update || typeof update !== "object") return null;

    // Preferred: update.pipeline.pii_spans
    const direct = update?.pipeline?.pii_spans;
    if (Array.isArray(direct)) return direct;

    // Fallback: scan patches
    for (const nodeName of Object.keys(update)) {
      const patch = update[nodeName];
      if (Array.isArray(patch?.pii_spans)) return patch.pii_spans;
    }
    return null;
  }

    function extractAuditFromMsgData(data: any): AuditEvent[] {
        const out: AuditEvent[] = [];
        const pipelineAudit = data?.pipeline?.audit_log;
        if (Array.isArray(pipelineAudit)) {
            for (const e of pipelineAudit) out.push(e);
            return out;
        }

        if (data && typeof data === "object") {
            for (const nodeName of Object.keys(data)) {
            const patch = data[nodeName];
            if (patch?.audit_log && Array.isArray(patch.audit_log)) {
                for (const e of patch.audit_log) out.push(e);
            }
            }
        }
        return out;
        }
    
    function fmtTs(ts_ms?: number) {
        if (!ts_ms) return "";
        return new Date(ts_ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        }

  return (
    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl space-y-4">
        <div className="rounded-2xl bg-white/70 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium">
            Question Generating Process
            {isLoading && (
              <div className="w-4 h-4 border-2 border-t-[#0956A9] border-gray-200 rounded-full animate-spin"></div>
            )}
          </div>
          <div className="text-sm text-gray-600">
            {isLoading ? "Running…" : done ? "Complete" : "In Progress..."}
          </div>
        </div>

          {currentStage && (
            <div className="mt-2 text-xs text-gray-600">
              Current stage: <span className="font-mono">{currentStage}</span>
            </div>
          )}

          {error && <div className="text-red-600 mt-2 text-sm">{error}</div>}

          {/* PII panel */}
          {piiSpans.length > 0 && (
            <div className="mt-4 rounded-xl border border-gray-200 bg-white p-3">
              <div className="text-xs font-medium mb-2">Redacted Personal Information</div>
              <ul className="text-xs text-gray-700 space-y-1">
                {piiSpans.map((s, i) => (
                  <li key={i}>
                    <span className="font-mono">{s.pii_type ?? "PII"}</span>
                    <span className="text-gray-500"> @ [{s.start ?? "?"},{s.end ?? "?"}]</span>
                    {typeof s.confidence === "number" && (
                      <span className="text-gray-500"> • conf {s.confidence.toFixed(2)}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Audit panel */}
          <div className="mt-4 rounded-xl border border-gray-200 bg-white p-3 max-h-80 overflow-auto">
            <div className="text-xs font-medium mb-2">Live updates</div>
            <ul className="space-y-1 text-xs text-gray-700">
              {audit.slice(-80).map((a, i) => (
                <li key={i} className="py-1">
                  <div>
                    <span className="text-gray-500">{fmtTs(a.ts_ms)}</span>
                    <span className="ml-2 font-mono">{a.agent ?? "?"}</span>
                    <span className="ml-2">{a.event ?? "update"}</span>

                    {a.agent === "validator" && a.event === "repair_planned" && (
                        <span className="ml-2 text-amber-700">
                        (regenerating: {(a.data?.beats_to_regen ?? []).join(", ")})
                        </span>
                    )}
                    </div>

                  {a.agent === "validator" && a.event === "repair_planned" && (
                    <div className="mt-1 ml-4 text-gray-600">
                      {/* Show compact reasons */}
                      {a.data?.failed_reasons && (
                        <div className="space-y-1">
                          {Object.entries(a.data.failed_reasons).map(([beat, reasons]: any) => (
                            <div key={beat}>
                              <span className="font-mono">{beat}</span>:{" "}
                              {Array.isArray(reasons) ? reasons.join(" • ") : String(reasons)}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Or show the exact format_response-style errors list */}
                      {Array.isArray(a.data?.errors) && a.data.errors.length > 0 && (
                        <div className="mt-2">
                          <div className="text-xs font-medium">Validator errors</div>
                          <ul className="list-disc ml-5">
                            {a.data.errors.map((e: string, idx: number) => (
                              <li key={idx}>{e}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              className="px-5 py-2 rounded-full bg-[#0956A9] text-white text-sm disabled:opacity-50 hover:bg-[#63A0E8] transition-colors"
              disabled={!done}
              onClick={() => router.push("/notepad/results")}
            >
              View questions →
            </button>

            <button
              className="px-5 py-2 rounded-full border border-[#0956A9] text-[#0956A9] text-sm hover:border-[#63A0E8] hover:text-[#63A0E8] transition-colors"
              onClick={() => router.push("/notepad")}
            >
              Start over
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}