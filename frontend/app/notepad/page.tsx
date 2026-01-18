"use client";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

export default function InputPage() {
  const router = useRouter();
  const [scholarship, setScholarship] = useState("");
  const [program, setProgram] = useState<"Undergrad" | "Graduate" | "Community Grant">("Undergrad");
  const [sentence, setSentence] = useState("");
  const [resume1, setResume1] = useState("");
  const [resume2, setResume2] = useState("");

  function onRun() {
    const payload = {
      scholarship_name: scholarship,
      program_type: program,
      goal_one_liner: sentence,
      resume_points: [resume1, resume2].filter(Boolean),
    };
    sessionStorage.setItem("pipeline_payload", JSON.stringify(payload));
    sessionStorage.removeItem("pipeline_result");
    router.push("/notepad/run");
  }

  return (
    <div className="min-h-screen pt-[120px] px-6 flex justify-center">
      <div className="w-full max-w-3xl rounded-2xl bg-white/70 p-8 space-y-4">
        <h1 className="text-xl font-medium">Start with the essentials</h1>

        <input className="w-full p-3 text-sm rounded-lg border" value={scholarship}
          onChange={(e) => setScholarship(e.target.value)} placeholder="Scholarship name" />

        <select className="w-full p-3 text-sm rounded-lg border bg-white"
          value={program} onChange={(e) => setProgram(e.target.value as any)}>
          <option value="Undergrad">Undergrad</option>
          <option value="Graduate">Graduate</option>
          <option value="Community Grant">Community Grant</option>
        </select>

        <textarea className="w-full p-3 text-sm rounded-lg border"
          value={sentence} onChange={(e) => setSentence(e.target.value)}
          placeholder="One-sentence thesis (most important)" />

        <input className="w-full p-3 text-sm rounded-lg border"
          value={resume1} onChange={(e) => setResume1(e.target.value)} placeholder="Resume point #1" />

        <input className="w-full p-3 text-sm rounded-lg border"
          value={resume2} onChange={(e) => setResume2(e.target.value)} placeholder="Resume point #2" />

        <button
          onClick={onRun}
          className="px-5 py-2 rounded-full bg-black text-white text-sm disabled:opacity-50"
          disabled={!scholarship || !sentence || !resume1}
        >
          Continue → stream run
        </button>
      </div>
    </div>
  );
}
