"use client";
import React, { useState, useEffect } from "react";
// import { PiiSanitizer } from '@cdssnc/sanitize-pii';

/* =====================
   Types
===================== */

type Step = 1 | 2 | 3;

type BeatKey = "A" | "B" | "C" | "D" | "E";

type Beat = {
  key: BeatKey;
  title: string;
  description: string;
  questions: string[];
};


/* =====================
   Page
===================== */

export default function QuestionEngine() {
  const [step, setStep] = useState<Step>(1);

  /* -------- Inputs -------- */
  const [scholarship, setScholarship] = useState("");
  const [program, setProgram] = useState("undergrad");
  const [sentence, setSentence] = useState("");
  const [resume1, setResume1] = useState("");
  const [resume2, setResume2] = useState("");

  /* -------- Writing -------- */
  const [answer, setAnswer] = useState("");
  const [visibleQuestions, setVisibleQuestions] = useState<Record<string, number>>({});

  /* -------- Beats -------- */
  const beats: Beat[] = [
    // {
    //   key: "A",
    //   title: "Purpose & Fit",
    //   description: "Why this scholarship, why now, why you.",
    //   questions: [
    //     "What specifically about this scholarship aligns with your goals right now?",
    //     "Why are you uniquely positioned to benefit from it?",
    //   ],
    // },
    // {
    //   key: "B",
    //   title: "Proof of Excellence",
    //   description: "Concrete evidence of ability and outcomes.",
    //   questions: [
    //     "What is one experience that best demonstrates your excellence?",
    //     "What measurable outcome resulted from your actions?",
    //   ],
    // },
    // {
    //   key: "C",
    //   title: "Impact / Community",
    //   description: "Who benefits and how change is created.",
    //   questions: [
    //     "Who benefits from your work beyond yourself?",
    //     "How would you measure the impact you create?",
    //   ],
    // },
    // {
    //   key: "D",
    //   title: "Leadership & Character",
    //   description: "Responsibility, tradeoffs, collaboration.",
    //   questions: [
    //     "Describe a difficult tradeoff you had to make.",
    //     "How did others rely on your judgment or leadership?",
    //   ],
    // },
    // {
    //   key: "E",
    //   title: "Reflection & Growth",
    //   description: "How your thinking has changed.",
    //   questions: [
    //     "What did this experience change about how you think?",
    //     "What will you carry forward from it?",
    //   ],
    // },
  ];

  /* =====================
     Effects
  ===================== */

//   // Gradually reveal questions when user types
//   useEffect(() => {
//     if (step !== 3) return;
//     if (answer.length < 40) return;

//     beats.forEach((beat) => {
//       if (!visibleQuestions[beat.key]) {
//         setVisibleQuestions((prev) => ({
//           ...prev,
//           [beat.key]: 1,
//         }));
//       }
//     });
//   }, [answer, step]);

  /* =====================
     Helpers
  ===================== */

  const restart = () => {
    setStep(1);
    setScholarship("");
    setSentence("");
    setResume1("");
    setResume2("");
    setAnswer("");
    setVisibleQuestions({});
  };

  /* =====================
     UI
  ===================== */

  return (
    <div className="min-h-screen pt-[140px] px-6 flex justify-center">
      <div className="w-full max-w-3xl relative">

        {/* Restart */}
        {step > 1 && (
          <button
            onClick={restart}
            className="absolute right-0 -top-8 text-xs text-gray-500 hover:text-black transition"
          >
            restart
          </button>
        )}

        {/* ================= STEP 1 ================= */}
        {step === 1 && (
          <div className="rounded-2xl bg-white/70 backdrop-blur p-8 shadow-sm space-y-6">
            <h1 className="text-xl font-medium">Start by filling out your information.</h1>

            <input
              className="w-full p-3 text-sm rounded-lg border border-gray-200 focus:outline-none"
              placeholder="Scholarship name"
              value={scholarship}
              onChange={(e) => setScholarship(e.target.value)}
            />

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
              className="mt-2 px-5 py-2 rounded-full bg-[#F34E39] text-white text-sm hover:opacity-80 transition"
            >
              continue
            </button>
          </div>
        )}

        {/* ================= STEP 2 ================= */}
        {step === 2 && (
          <div className="rounded-2xl bg-white/70 p-8 space-y-4 text-sm">
            <h2 className="font-medium">Quick system checks</h2>

            <p className="text-gray-600">PII scan complete</p>
            <p className="text-gray-600">Inputs validated</p>
            <p className="text-green-700">✓ Ready to generate questions</p>

            <button
              onClick={() => setStep(3)}
              className="mt-4 px-5 py-2 rounded-full bg-[#F34E39] text-white text-sm hover:opacity-80 transition"
            >
              begin writing
            </button>
          </div>
        )}

        {/* ================= STEP 3 ================= */}
        {step === 3 && (
          <div className="space-y-10">

            {/* Answer box */}
            <textarea
              className="w-full min-h-[140px] p-4 text-sm rounded-xl border border-gray-200 focus:outline-none"
              placeholder="Start writing."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
            />

            {/* Beats */}
            {beats.map((beat) => (
              <div key={beat.key} className="space-y-2">
                <h3 className="text-sm font-medium">
                  {beat.title}
                  <span className="text-gray-400 font-normal ml-2">
                    {beat.description}
                  </span>
                </h3>

                <div className="space-y-2">
                  {beat.questions
                    .slice(0, visibleQuestions[beat.key] || 0)
                    .map((q, i) => (
                      <div
                        key={i}
                        className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg animate-fade-in"
                      >
                        {q}
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Fade animation */}
      <style jsx>{`
        .animate-fade-in {
          animation: fadeIn 0.6s ease forwards;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
