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

  // **Load saved payload when coming back from /notepad/run**
  useEffect(() => {
    const saved = sessionStorage.getItem("pipeline_payload");
    if (saved) {
      try {
        const data = JSON.parse(saved);
        if (data.scholarship_name) setScholarship(data.scholarship_name);
        if (data.program_type) setProgram(data.program_type);
        if (data.goal_one_liner) setSentence(data.goal_one_liner);
        if (Array.isArray(data.resume_points)) {
          setResume1(data.resume_points[0] || "");
          setResume2(data.resume_points[1] || "");
          setResume3(data.resume_points[2] || "");
        }
      } catch {
        // If parsing fails, ignore
      }
    }
  }, []);

  function clearErrors() {
    setFieldErrors({});
    setBannerError(null);
  }

  function payload() {
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
    sessionStorage.setItem("pipeline_payload", JSON.stringify(body));
    sessionStorage.removeItem("pipeline_result");

    try {
      const res = await fetch("/api/pipeline/run_stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const txt = await res.text();
        const firstLine = txt.split("\n").find((l) => l.trim());
        try {
          const j = firstLine ? JSON.parse(firstLine) : null;
          if (j?.type === "error" && j?.error === "INPUT_VALIDATION") {
            const data: ValidationPayload = j.data || {};
            setBannerError(data.summary || "Please fix the highlighted fields.");
            setFieldErrors(data.field_errors || {});
            return;
          }
        } catch {}
        setBannerError("Something looks off with the input. Please add more detail to your answers and try again.");
        return;
      }

      router.push("/notepad/run");
    } catch {
      setBannerError("Network error. Please try again.");
    } finally {
      setIsChecking(false);
    }
  }

  const fe = fieldErrors;

  const inputStyle =
    "w-full p-3 text-sm rounded-lg border placeholder-gray-400 text-[#0956A9] border-[#0956A9]";

  return (

    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl rounded-2xl bg-white/70 p-8 space-y-4">
        <h1 className="text-xl font-medium">To start, fill in the following information</h1>

        {bannerError && (
          <div className="rounded-xl border border-red-200 bg-white p-3 text-sm text-red-700">
            {bannerError}
          </div>
        )}

        <div>
          <label className="block mb-1 font-medium text-[0.7rem]">Scholarship Name</label>
          <input
            className={inputStyle}
            value={scholarship}
            onChange={(e) => setScholarship(e.target.value)}
            placeholder="Ex: Fulbright Scholarship"
          />
          {fe.scholarship_name?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <div>
          <label className="block mb-1 font-medium text-[0.7rem]">Program Type</label>
          <select
            className={`w-full p-3 text-sm rounded-lg border bg-white text-[#0956A9] border-[#0956A9]`}
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
          <label className="block mb-1 font-medium text-[0.7rem]">One-Sentence Thesis</label>
          <textarea
            className={inputStyle}
            value={sentence}
            onChange={(e) => setSentence(e.target.value)}
            placeholder="Ex: I aim to improve community healthcare access using AI."
          />
          {fe.goal_one_liner?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <div>
          <label className="block mb-1 font-medium text-[0.7rem]">Resume Point #1</label>
          <textarea
            className={inputStyle}
            value={resume1}
            onChange={(e) => setResume1(e.target.value)}
            placeholder="Ex: Led a 10-person project team in college."
          />
        </div>

        <div>
          <label className="block mb-1 font-medium text-[0.7rem]">Resume Point #2</label>
          <textarea
            className={inputStyle}
            value={resume2}
            onChange={(e) => setResume2(e.target.value)}
            placeholder="Ex: Published research on renewable energy solutions."
          />
        </div>

        <div>
          <label className="block mb-1 font-medium text-[0.7rem]">Resume Point #3</label>
          <textarea
            className={inputStyle}
            value={resume3}
            onChange={(e) => setResume3(e.target.value)}
            placeholder="Ex: Volunteer experience at local food bank."
          />
          {fe.resume_points?.map((m, i) => (
            <div key={i} className="text-xs text-red-600 mt-1">{m}</div>
          ))}
        </div>

        <div className="flex gap-4 mt-4">
  <button
    onClick={validateAndRun}
    className="px-5 py-2 rounded-full bg-[#0956A9] text-white text-sm disabled:opacity-50 hover:bg-[#63A0E8] transition-colors"
    disabled={isChecking || !scholarship || !sentence || !resume1 || !resume2 || !resume3}
  >
    {isChecking ? "Checking…" : "Submit"}
  </button>

        <button
          type="button"
          onClick={() => {
            setScholarship("");
            setProgram("Undergrad");
            setSentence("");
            setResume1("");
            setResume2("");
            setResume3("");
            clearErrors();
            sessionStorage.removeItem("pipeline_payload");
          }}
          className="px-5 py-2 rounded-full border border-[#0956A9] bg-white text-[#0956A9] text-sm hover:bg-[#63A0E8] hover:text-white transition-colors"
        >
          Clear
        </button>
      </div>
      </div>
    </div>
    
  );
}
