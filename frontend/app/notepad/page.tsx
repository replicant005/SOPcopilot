"use client";
import { useRouter } from "next/navigation";
import React, { useState, useEffect } from "react";

type Program = "Undergrad" | "Graduate" | "Community Grant";

type ValidationPayload = {
  summary?: string;
  field_errors?: Record<string, string[]>;
};

export default function InputPage() {
  const router = useRouter();

  const [scholarship, setScholarship] = useState("");
  const [program, setProgram] = useState<Program>("Undergrad");
  const [sentence, setSentence] = useState("");
  const [resume1, setResume1] = useState("");
  const [resume2, setResume2] = useState("");
  const [resume3, setResume3] = useState("");

  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [bannerError, setBannerError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  // Load values from sessionStorage on mount to persist text during user session
  useEffect(() => {
    const raw = sessionStorage.getItem("pipeline_payload");
    if (raw) {
      try {
        const payload = JSON.parse(raw);
        if (payload.scholarship_name) setScholarship(payload.scholarship_name);
        if (payload.program_type) setProgram(payload.program_type);
        if (payload.goal_one_liner) setSentence(payload.goal_one_liner);
        if (payload.resume_points?.[0]) setResume1(payload.resume_points[0]);
        if (payload.resume_points?.[1]) setResume2(payload.resume_points[1]);
        if (payload.resume_points?.[2]) setResume3(payload.resume_points[2]);
      } catch (e) {
        console.error("Failed to load saved form data", e);
      }
    }
  }, []);

  function clearErrors() {
    setFieldErrors({});
    setBannerError(null);
  }

  function payload() {
    // include resume3 if you want it counted; right now your backend requires min 2 points
    const resume_points = [resume1, resume2, resume3].filter((x) => x.trim().length > 0);

    return {
      scholarship_name: scholarship,
      program_type: program,
      goal_one_liner: sentence,
      resume_points,
    };
  }

  async function validateAndRun() {
    clearErrors();
    setIsChecking(true);

    const body = payload();

    // Save payload up-front so /notepad/run can use it if validation passes
    sessionStorage.setItem("pipeline_payload", JSON.stringify(body));
    sessionStorage.removeItem("pipeline_result");

    try {
      // Preflight: hit the same endpoint but we only care about validation
      const res = await fetch("/api/pipeline/run_stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      // If validation fails, backend should respond 400 + NDJSON error line.
      if (!res.ok) {
        const txt = await res.text();
        const firstLine = txt.split("\n").find((l) => l.trim());

        try {
          const j = firstLine ? JSON.parse(firstLine) : null;

          // Expected shape: { type:"error", error:"INPUT_VALIDATION", data:{summary, field_errors} }
          if (j?.type === "error" && j?.error === "INPUT_VALIDATION") {
            const data: ValidationPayload = j.data || {};
            setBannerError(data.summary || "Please fix the highlighted fields.");
            setFieldErrors(data.field_errors || {});
            return; // IMPORTANT: do not navigate
          }
        } catch {
          // fall through to generic message below
        }

        // Generic message (never show raw HTTP dump to user)
        setBannerError("Something looks off with the input. Please review and try again.");
        return;
      }

      // If we got here, validation passed and streaming can start
      router.push("/notepad/run");
    } catch {
      setBannerError("Network error. Please try again.");
    } finally {
      setIsChecking(false);
    }
  }

  const fe = fieldErrors;

  return (
    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl rounded-2xl bg-white/70 p-8 space-y-4">
        <h1 className="text-xl font-medium">Start with the essentials</h1>

        {bannerError && (
          <div className="rounded-xl border border-red-200 bg-white p-3 text-sm text-red-700">
            {bannerError}
          </div>
        )}

        <div>
          <input
            className="w-full p-3 text-sm rounded-lg border"
            value={scholarship}
            onChange={(e) => setScholarship(e.target.value)}
            placeholder="Scholarship name"
          />
          {fe.scholarship_name?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <div>
          <select
            className="w-full p-3 text-sm rounded-lg border bg-white"
            value={program}
            onChange={(e) => setProgram(e.target.value as Program)}
          >
            <option value="Undergrad">Undergrad</option>
            <option value="Graduate">Graduate</option>
            <option value="Community Grant">Community Grant</option>
          </select>
          {fe.program_type?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <div>
          <textarea
            className="w-full p-3 text-sm rounded-lg border"
            value={sentence}
            onChange={(e) => setSentence(e.target.value)}
            placeholder="One-sentence thesis"
          />
          {fe.goal_one_liner?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <div>
          <input
            className="w-full p-3 text-sm rounded-lg border"
            value={resume1}
            onChange={(e) => setResume1(e.target.value)}
            placeholder="Resume point #1"
          />
        </div>

        <div>
          <input
            className="w-full p-3 text-sm rounded-lg border"
            value={resume2}
            onChange={(e) => setResume2(e.target.value)}
            placeholder="Resume point #2"
          />
        </div>

        <div>
          <input
            className="w-full p-3 text-sm rounded-lg border"
            value={resume3}
            onChange={(e) => setResume3(e.target.value)}
            placeholder="Resume point #3"
          />
          {/* List-level errors (e.g., need >=2 points) */}
          {fe.resume_points?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <button
          onClick={validateAndRun}
          className="px-5 py-2 rounded-full bg-black text-white text-sm disabled:opacity-50"
          disabled={isChecking || !scholarship || !sentence || !resume1}
        >
          {isChecking ? "Checking…" : "Continue → stream run"}
        </button>
      </div>
    </div>
  );
}

