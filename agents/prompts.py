from textwrap import dedent

def _beat_defs() -> str:
    return dedent("""\
    Beats:
    A: Purpose & Fit
    B: Excellence / Proof
    C: Impact
    D: Leadership & Character
    E: Reflection & Growth
    """)

def beat_planner_messages(redacted_input: str):
    system = dedent("""\
    You are a beat planner for an SOP question generator.
    Return structured data only. No prose.
    """)

    rules = dedent("""\
    Create a plan for beats A–E.

    For each beat output:
    - beat: one of A,B,C,D,E
    - missing: 2–4 short, specific missing details needed to write that beat,
      grounded in the redacted input (reference the section name when possible).
    - guidance: one actionable hint (<= 20 words).
    - anchors: 2–4 exact phrases copied verbatim from the redacted input (each <= 6 words)
      that are relevant to this beat.

    Constraints:
    - Include A,B,C,D,E exactly once.
    - If the input lacks anchors for a beat, set anchors=[] and put the needed specifics in missing.
    """)

    user_ctx = dedent(f"""\
    {_beat_defs()}
    Redacted canonical input (source of truth):
    {redacted_input}

    Return a beat plan.
    """)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": rules + "\n\n" + user_ctx},
    ]

def question_generator_messages(task, redacted_input: str):
    system = dedent("""\
    You generate tailored SOP questions.
    Return structured data only. No prose.
    """)

    regen_mode = bool(task.guidance and "Regenerate questions" in task.guidance)

    base_rules = dedent("""\
    Generate exactly 2 questions for the given beat.

    Output format:
    {
      "beat": "A|B|C|D|E",
      "questions": [
        {"q": "...?", "intent": "...", "anchor_used": "..."},
        {"q": "...?", "intent": "...", "anchor_used": "..."}
      ]
    }

    Constraints:
    - Structured data only.
    - Questions only: each q must be a single line ending with '?'.
    - Do NOT include any PII or placeholders like <NAME>, <EMAIL>, <PHONE>, [ORG_1].
    - intent must be <= 12 words and describe what the question tests.
    - beat must equal the provided beat.
    - Keep wording concise.
    - The two questions must be meaningfully different:
      * Q1: narrative/decision/tradeoff
      * Q2: evidence/validation/comparison/feedback signal
    """)

    grounding_rules = dedent("""\
    Grounding rules:
    - Do NOT introduce specific names, organizations, dates, locations, or numbers
      unless they appear verbatim in the provided redacted input.
    - If a specific detail is missing, ask for it instead of assuming it.
    """)

    anti_generic_rules = dedent("""\
    Anti-generic rules:
    - Each question must be anchored: it must include an exact short phrase from task.anchors
      (verbatim) OR explicitly reference a specific section/item from the redacted input
      (e.g., “Experience Inventory #2”).
    - Avoid generic openers like “Tell me about a time…” unless tied to a named anchor.
    - No filler: every question must point to a concrete story, decision, or evidence.
    """)

    regen_rules = dedent("""\
    Regeneration rule:
    - Previous output failed validation. Make questions more grounded and less assumption-heavy.
    - Prefer asking for missing details rather than stating facts.
    """) if regen_mode else ""

    beat_ctx = dedent(f"""\
    Beat: {task.beat}
    Missing: {task.missing}
    Guidance: {task.guidance}
    Anchors: {getattr(task, "anchors", [])}
    """)

    user = dedent(f"""\
    {_beat_defs()}
    {beat_ctx}

    Redacted input (source of truth):
    {redacted_input}
    """)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": base_rules + grounding_rules + anti_generic_rules + regen_rules + "\n\n" + user},
    ]