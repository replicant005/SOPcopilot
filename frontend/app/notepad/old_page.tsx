"use client";
import React, { useMemo, useState } from "react";

type Step = 1 | 2 | 3;
type BeatKey = "A" | "B" | "C" | "D" | "E";

type QuestionObject = { beat: BeatKey; question: string; intent: string };

type PipelineResponse = {
  final_questions_by_beat: Record<BeatKey, QuestionObject[]>;
  validation_report?: { ok: boolean; errors?: string[]; warnings?: string[]; repairs_applied?: string[] };
  audit_log?: { ts_ms: number; agent: string; event: string; data: any }[];
};

type AuditEvent = { ts_ms?: number; agent?: string; event?: string; data?: any; raw?: any };

export default function QuestionEngine() {
  const [step, setStep] = useState<Step>(1);

  /* -------- Inputs -------- */
  const [scholarship, setScholarship] = useState("");
  const [program, setProgram] = useState<"Undergrad" | "Graduate" | "Community Grant">("Undergrad");
  const [sentence, setSentence] = useState("");
  const [resume1, setResume1] = useState("");
  const [resume2, setResume2] = useState("");

  /* -------- Pipeline outputs -------- */
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  

  const beatsMeta = useMemo(
    () => ([
      { key: "A" as const, title: "Purpose & Fit", description: "Why this scholarship, why now, why you." },
      { key: "B" as const, title: "Proof of Excellence", description: "Concrete evidence of ability and outcomes." },
      { key: "C" as const, title: "Impact / Community", description: "Who benefits and how change is created." },
      { key: "D" as const, title: "Leadership & Character", description: "Responsibility, tradeoffs, collaboration." },
      { key: "E" as const, title: "Reflection & Growth", description: "How your thinking has changed." },
    ]),
    []
  );

  const restart = () => {
    setStep(1);
    setScholarship("");
    setProgram("Undergrad");
    setSentence("");
    setResume1("");
    setResume2("");
    setIsLoading(false);
    setError(null);
    setAudit([]);
    setResult(null);
  };

  async function runPipelineStream() {
    setIsLoading(true);
    setError(null);
    setAudit([]);
    setResult(null);

    const payload = {
      scholarship_name: scholarship,
      program_type: program,
      goal_one_liner: sentence,
      resume_points: [resume1, resume2].filter(Boolean),
    };

    try {
      const res = await fetch("/api/pipeline/run_stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }
      if (!res.body) throw new Error("No response body (stream unsupported?)");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // NDJSON: split by newline
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          const msg = JSON.parse(line);

          if (msg.type === "update") {
            // Your update may contain node patches, including audit_log patches.
            // We can extract audit_log if present; otherwise store raw update.
            const update = msg.data;
            const maybeAudit = extractAuditFromUpdate(update);
            if (maybeAudit.length) {
              setAudit((prev) => [...prev, ...maybeAudit]);
            } else {
              setAudit((prev) => [...prev, { raw: update }]);
            }
          } else if (msg.type === "result") {
            setResult(msg.data as PipelineResponse);
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

  function extractAuditFromUpdate(update: any): AuditEvent[] {
    // updates are usually: { nodeName: { ...patch... } }
    // your patch will look like: { audit_log: [ {...}, ... ] }
    const out: AuditEvent[] = [];
    if (!update || typeof update !== "object") return out;

    for (const nodeName of Object.keys(update)) {
      const patch = update[nodeName];
      if (patch?.audit_log && Array.isArray(patch.audit_log)) {
        for (const entry of patch.audit_log) out.push(entry);
      } else {
        // fallback: show stage transitions
        out.push({ agent: nodeName, event: "update", data: patch });
      }
    }
    return out;
  }

  const finalByBeat = result?.final_questions_by_beat;

  return (
    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl relative">
        {step > 1 && (
          <button
            onClick={restart}
            className="absolute right-0 -top-8 text-xs text-gray-500 hover:text-black transition"
          >
            restart
          </button>
        )}

        {/* STEP 1 */}
        {step === 1 && (
          <div className="rounded-2xl bg-white/70 backdrop-blur p-8 shadow-sm space-y-6">
            <h1 className="text-xl font-medium">Start with the essentials</h1>

            <input
              className="w-full p-3 text-sm rounded-lg border border-gray-200 focus:outline-none"
              placeholder="Scholarship name"
              value={scholarship}
              onChange={(e) => setScholarship(e.target.value)}
            />

            {/* Optional: program type selector */}
            <select
              className="w-full p-3 text-sm rounded-lg border border-gray-200 focus:outline-none bg-white"
              value={program}
              onChange={(e) => setProgram(e.target.value as any)}
            >
              <option value="Undergrad">Undergrad</option>
              <option value="Graduate">Graduate</option>
              <option value="Community Grant">Community Grant</option>
            </select>

            <textarea
              className="w-full p-3 text-sm rounded-lg border border-gray-200"
              placeholder="One-sentence thesis (most important)"
              value={sentence}
              onChange={(e) => setSentence(e.target.value)}
            />

            <input
              className="w-full p-3 text-sm rounded-lg border border-gray-200"
              placeholder="Resume point #1"
              value={resume1}
              onChange={(e) => setResume1(e.target.value)}
            />

            <input
              className="w-full p-3 text-sm rounded-lg border border-gray-200"
              placeholder="Resume point #2"
              value={resume2}
              onChange={(e) => setResume2(e.target.value)}
            />

            <button
              onClick={() => setStep(2)}
              className="mt-2 px-5 py-2 rounded-full bg-black text-white text-sm hover:opacity-80 transition"
              disabled={!scholarship || !sentence || !resume1}
            >
              continue
            </button>
          </div>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <div className="rounded-2xl bg-white/70 p-8 space-y-4 text-sm">
            <h2 className="font-medium">Run pipeline</h2>

            <div className="flex gap-3 items-center">
              <button
                onClick={async () => {
                  setStep(3);
                  await runPipelineStream();
                }}
                className="px-5 py-2 rounded-full bg-black text-white text-sm hover:opacity-80 transition disabled:opacity-50"
                disabled={isLoading}
              >
                {isLoading ? "generating..." : "generate questions"}
              </button>

              {error && <span className="text-red-600 text-xs">{error}</span>}
            </div>

            <div className="text-gray-600">
              {isLoading ? "Streaming audit log..." : "Ready."}
            </div>

            {/* Mini audit feed in step 2 */}
            {audit.length > 0 && (
              <div className="mt-4 rounded-xl border border-gray-200 bg-white p-3 max-h-48 overflow-auto">
                <div className="text-xs font-medium mb-2">Workflow stages</div>
                <ul className="space-y-1 text-xs text-gray-700">
                  {audit.slice(-25).map((a, i) => (
                    <li key={i}>
                      <span className="text-gray-500">{a.agent ?? "?"}</span>
                      {" — "}
                      <span>{a.event ?? "update"}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <div className="space-y-8">
            {/* Loading / status */}
            <div className="rounded-2xl bg-white/70 p-6 text-sm">
              <div className="flex items-center justify-between">
                <div className="font-medium">Generated Questions</div>
                {isLoading ? (
                  <div className="text-gray-600">Running pipeline…</div>
                ) : result?.validation_report?.ok ? (
                  <div className="text-green-700">✓ Validated</div>
                ) : (
                  <div className="text-gray-600">Done</div>
                )}
              </div>

              {error && <div className="text-red-600 mt-2">{error}</div>}

              {audit.length > 0 && (
                <div className="mt-4 rounded-xl border border-gray-200 bg-white p-3 max-h-56 overflow-auto">
                  <div className="text-xs font-medium mb-2">Audit log (live)</div>
                  <ul className="space-y-1 text-xs text-gray-700">
                    {audit.slice(-60).map((a, i) => (
                      <li key={i}>
                        <span className="text-gray-500">{a.ts_ms ?? ""}</span>{" "}
                        <span className="font-mono">{a.agent ?? "?"}</span>{" "}
                        <span>{a.event ?? "update"}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Beats + questions */}
            {beatsMeta.map((beat) => {
              const qs = finalByBeat?.[beat.key] ?? [];
              return (
                <div key={beat.key} className="space-y-2">
                  <h3 className="text-sm font-medium">
                    {beat.title}
                    <span className="text-gray-400 font-normal ml-2">
                      {beat.description}
                    </span>
                  </h3>

                  <div className="space-y-2">
                    {isLoading && qs.length === 0 && (
                      <div className="text-xs text-gray-500">waiting for {beat.key}…</div>
                    )}

                    {qs.map((qo, i) => (
                      <div key={i} className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                        <div>{qo.question}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          Intent: {qo.intent}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
