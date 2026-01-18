"use client";
import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type BeatKey = "A" | "B" | "C" | "D" | "E";
type QuestionObject = { beat: BeatKey; question: string; intent: string };

type PipelineResponse = {
  final_questions_by_beat: Record<BeatKey, QuestionObject[]>;
  validation_report?: { ok: boolean; errors?: string[]; warnings?: string[]; repairs_applied?: string[] };
  audit_log?: { ts_ms: number; agent: string; event: string; data: any }[];
};

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<PipelineResponse | null>(null);

  // answers keyed by "A-0", "B-2", etc.
  const [answers, setAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    const raw = sessionStorage.getItem("pipeline_result");
    if (!raw) {
      router.push("/"); // nothing to show
      return;
    }
    setResult(JSON.parse(raw));
  }, [router]);

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

  const finalByBeat = result?.final_questions_by_beat;

  function setAnswer(key: string, v: string) {
    setAnswers((prev) => ({ ...prev, [key]: v }));
  }

  function exportAnswers() {
    const blob = new Blob([JSON.stringify({ answers }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sop_answers.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl space-y-6">
        <div className="rounded-2xl bg-white/70 p-6 text-sm">
          <div className="flex items-center justify-between">
            <div className="font-medium">Final questions + draft space</div>
            <div className="flex gap-2">
              <button className="px-4 py-2 rounded-full border text-sm" onClick={() => router.push("/notepad/run")}>
                Back to stream
              </button>
              <button className="px-4 py-2 rounded-full bg-black text-white text-sm" onClick={exportAnswers}>
                Export answers
              </button>
            </div>
          </div>
          {result?.validation_report?.ok ? (
            <div className="text-green-700 mt-2">✓ Validated</div>
          ) : (
            <div className="text-gray-600 mt-2">Done</div>
          )}
        </div>

        {beatsMeta.map((beat) => {
          const qs = finalByBeat?.[beat.key] ?? [];
          return (
            <div key={beat.key} className="space-y-2">
              <h3 className="text-sm font-medium">
                {beat.title}
                <span className="text-gray-400 font-normal ml-2">{beat.description}</span>
              </h3>

              <div className="space-y-4">
                {qs.map((qo, i) => {
                  const k = `${beat.key}-${i}`;
                  return (
                    <div key={k} className="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
                      <div className="text-sm text-gray-900">{qo.question}</div>
                      <div className="text-xs text-gray-500">Intent: {qo.intent}</div>

                      <textarea
                        className="w-full min-h-[96px] p-3 text-sm rounded-lg border border-gray-200"
                        placeholder="Write your answer here…"
                        value={answers[k] ?? ""}
                        onChange={(e) => setAnswer(k, e.target.value)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
