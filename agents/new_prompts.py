from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Dict, List, Optional

from agents.models import BeatPlanItem

@dataclass(frozen=True)
class PromptProfile:
    """
    A prompt profile defines:
      - beat definitions (A–E meaning)
      - beat planner system/rules
      - question generator system/rules (+ optional program-specific extras)
    """
    beat_defs: str
    beat_planner_system: str
    beat_planner_rules: str
    question_system: str
    question_rules: str


def _has_sponsor_lens(redacted_input: str) -> bool:
    # Cheap, deterministic detection. Avoid regex to keep it simple.
    # You can standardize the header in your redacted input canonicalizer.
    return "[SPONSOR LENS" in redacted_input.upper()


def _define_beats(program_type: str) -> str:
    if program_type == "Community Grant":
        return dedent("""\
        Beats (Community Grant SOP):
        A: Community Need & Alignment
           - What need exists, who is affected, why now, and why your project fits the grant’s priorities.
        B: Project Plan & Feasibility
           - What you will do, how you will do it, timeline, resources, budget, and realistic execution.
        C: Impact & Measurement
           - What changes, for whom, how much, and how you’ll measure/validate success.
        D: Team, Partners & Safeguards
           - Who is doing what, partner roles, permissions, logistics, risk management, safety/ethics.
        E: Sustainability & Learning
           - What happens after funding, maintenance/hand-off, scalability, and what you learned/changed.
        """)
    elif program_type == "Graduate":
        # TODO: Replace with real beat defs for grad SOP.
        return dedent("""\
        Beats (Graduate SOP - placeholder):
        A: Purpose & Fit
        B: Excellence / Proof
        C: Impact
        D: Leadership & Character
        E: Reflection & Growth
  
        For example, the user may (a) be applying to a PhD (research) program and \
        (b) have research experience on their resume. Suppose you are working on beat A: Purpose & Fit. \
        In this case, you should output anchors to both the fact that the PhD is a research program and \
        their past experience in research. You may say that missing information includes the research \
        fit between the two, or the motivation the user has to commit to a research program.
        """)
    else:
        raise Exception("Unknown scholarship type is passed.")


def _default_profile(program_type: str) -> PromptProfile:
    # Baseline prompts that work for any program_type, but are less specialized.
    beat_defs = _define_beats(program_type)

    beat_planner_system = dedent(f"""\
    You are a beat planner for a Statement of Purpose question generator.
    Target program type: {program_type}.
    A "beat" is a section-level point/story the applicant must write around.
    Return structured data only. No prose.
    """)

    beat_planner_rules = dedent("""\
    Create a plan for beats A–E (include each beat exactly once).

    For each beat output:
    - beat: A|B|C|D|E
    - missing: 2–4 concrete missing details needed to write that beat
    - guidance: one actionable hint (<= 20 words)
    - anchors: 2–4 exact short phrases copied verbatim from the redacted input (<= 8 words each)
    - ask_for: 2–4 atomic details the question generator must ask the user to provide

    Constraints:
    - missing and ask_for MUST be grounded in the provided redacted input (no assumptions).
    - If the input provides no good anchors for a beat, set anchors=[] and put the needed specifics in missing/ask_for.
    - anchors MUST be copied verbatim from the redacted input (case-sensitive substring).
    """)

    question_system = dedent("""\
    You generate tailored questions to help an applicant write their Statement of Purpose.
    Return structured data only. No prose.
    """)

    question_rules = dedent("""\
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
    - Output structured data only.
    - Questions only: each q must be a single line ending with '?'.
    - Do NOT include any PII or placeholders like <NAME>, <EMAIL>, <PHONE>, [ORG_1].
    - intent must be short (<= 12 words) and describe what the question tests.
    - beat must equal the provided beat.
    - Keep wording concise.
    - The two questions must be meaningfully different:
      * Q1: narrative/decision/tradeoff
      * Q2: evidence/validation/comparison/feedback signal

    Grounding rules:
    - Do NOT introduce specific names, organizations, dates, locations, or numbers unless they appear verbatim in the redacted input.
    - If a specific detail is missing, ask for it instead of assuming it.

    Anti-generic rules:
    - Each question must be anchored: it must include an exact short phrase from task.anchors (verbatim)
      OR explicitly reference a specific section/item from the redacted input (e.g., “PROJECT SNAPSHOT”).
    - Avoid generic openers like “Tell me about a time…” unless tied to a named anchor.
    - No filler: every question must point to a concrete story, decision, or evidence.
    """)

    return PromptProfile(
        beat_defs=beat_defs,
        beat_planner_system=beat_planner_system,
        beat_planner_rules=beat_planner_rules,
        question_system=question_system,
        question_rules=question_rules,
    )


def _community_grant_profile(program_type: str, redacted_input: str) -> PromptProfile:
    """
    Community Grant specialization:
      - Forces sponsor-alignment extraction if a Sponsor Lens section exists
      - Forces feasibility, budget, safeguards, and measurement specificity
    """
    beat_defs = _define_beats(program_type)
    sponsor_lens_present = _has_sponsor_lens(redacted_input)

    beat_planner_system = dedent("""\
    You are a beat planner for a COMMUNITY GRANT Statement of Purpose (SOP) question generator.
    The goal is to produce non-generic, funder-aligned questions by identifying missing grant-critical details.
    Return structured data only. No prose.
    """)

    beat_planner_rules = dedent(f"""\
    Create a plan for beats A–E (include each beat exactly once).

    For each beat output:
    - beat: A|B|C|D|E
    - missing: 2–4 concrete missing details needed to write that beat
      (reference the redacted input section names when possible).
    - guidance: one actionable hint (<= 20 words), grant-writing oriented.
    - anchors: 2–4 exact short phrases copied verbatim from the redacted input (<= 8 words each)
      that the question generator can reuse to stay specific.
    - ask_for: 2–4 atomic details the question generator must ask the user to provide.

    Community grant emphasis (apply where relevant):
    - Need clarity: who is affected + why now + local context.
    - Feasibility: steps + timeline + roles + required permissions + budget line items.
    - Measurement: concrete success signals + how they’ll be tracked.
    - Safeguards: safety/ethics/logistics/risk management.
    - Sustainability: what happens after funding + handoff/maintenance.

    Sponsor fit rule:
    - {"If a [SPONSOR LENS] section exists, Beat A must include at least 1 anchor from it and at least 1 missing/ask_for item about alignment." if sponsor_lens_present else "If a sponsor-priorities section exists, use it as anchors; otherwise, focus on user-provided grant priorities."}

    Constraints:
    - missing and ask_for MUST be grounded in the redacted input (no assumptions).
    - If no anchors exist for a beat, set anchors=[] and put the needed specifics in missing/ask_for.
    - anchors MUST be copied verbatim from the redacted input (case-sensitive substring).
    """)

    question_system = dedent("""\
    You generate tailored COMMUNITY GRANT SOP questions.
    Your questions must elicit concrete grant-ready details: need, plan, budget, safeguards, measurement, sustainability.
    Return structured data only. No prose.
    """)

    sponsor_extra = dedent("""\
    Sponsor-fit requirement:
    - A [SPONSOR LENS] section exists in the redacted input.
    - For Beat A, at least one question must explicitly reference "[SPONSOR LENS" and ask for a concrete alignment mapping
      (what you will do that matches those priorities/examples).
    """) if sponsor_lens_present else dedent("""\
    Sponsor-fit requirement:
    - If any sponsor/grant priorities are present in the redacted input, Beat A must ask for a direct mapping to them.
    """)

    question_rules = dedent(f"""\
    Generate exactly 2 questions for the given beat.

    Output format:
    {{
      "beat": "A|B|C|D|E",
      "questions": [
        {{"q": "...?", "intent": "...", "anchor_used": "..."}},
        {{"q": "...?", "intent": "...", "anchor_used": "..."}}
      ]
    }}

    Constraints:
    - Output structured data only.
    - Questions only: each q must be a single line ending with '?'.
    - Do NOT include any PII or placeholders like <NAME>, <EMAIL>, <PHONE>, [ORG_1].
    - intent must be <= 12 words and describe what the question tests.
    - beat must equal the provided beat.
    - Keep wording concise.
    - The two questions must be meaningfully different:
      * Q1: narrative/decision/tradeoff (why this approach, why now, key choice)
      * Q2: evidence/measurement/feasibility (how you’ll validate, track, or execute)

    Grounding rules:
    - Do NOT introduce specific names, organizations, dates, locations, or numbers unless they appear verbatim in the redacted input.
    - If a specific detail is missing, ask for it instead of assuming it.

    Anti-generic rules (strict):
    - Each question MUST be anchored:
      * It must include an exact short phrase from task.anchors verbatim (set anchor_used to that exact phrase),
        OR explicitly reference a specific redacted input section (e.g., “PROJECT SNAPSHOT”, “PLAN”, “IMPACT & MEASUREMENT”).
    - If task.anchors is non-empty, prefer using an anchor (anchor_used should not be empty).
    - No filler: every question must force a concrete grant-ready detail (deliverable, timeline step, risk, metric, budget line item).

    Community-grant targeting:
    - Beat B: ensure at least one question requests steps + timeline + resources/budget at a practical level.
    - Beat C: ensure at least one question requests a measurement plan (metric + method + cadence).
    - Beat D: ensure at least one question requests roles + partner permissions + safeguards/risks.
    - Beat E: ensure at least one question requests post-funding sustainability/hand-off.

    {sponsor_extra.strip()}
    """)

    return PromptProfile(
        beat_defs=beat_defs,
        beat_planner_system=beat_planner_system,
        beat_planner_rules=beat_planner_rules,
        question_system=question_system,
        question_rules=question_rules,
    )


def get_prompt_profile(program_type: str, redacted_input: str) -> PromptProfile:
    """
    Central switch: add more program types here without touching the agent logic.
    """
    if program_type == "Community Grant":
        return _community_grant_profile(program_type, redacted_input)
    # elif program_type == "Graduate":
    #     return _graduate_profile(program_type, redacted_input)  # TODO
    return _default_profile(program_type)


def beat_planner_messages(program_type: str, redacted_input: str) -> List[Dict[str, Any]]:
    profile = get_prompt_profile(program_type, redacted_input)

    user_ctx = dedent(f"""\
    {profile.beat_defs}
    Redacted canonical input (source of truth):
    {redacted_input}

    Return a beat plan.
    """)

    return [
        {"role": "system", "content": profile.beat_planner_system},
        {"role": "user", "content": profile.beat_planner_rules + "\n\n" + user_ctx},
    ]


def question_generator_messages(task: BeatPlanItem, program_type: str, redacted_input: str) -> List[Dict[str, Any]]:
    profile = get_prompt_profile(program_type, redacted_input)

    regen_mode = bool(task.guidance and "Regenerate questions" in task.guidance)
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

    user_ctx = dedent(f"""\
    {profile.beat_defs}
    {beat_ctx}

    Redacted input (source of truth):
    {redacted_input}
    """)

    return [
        {"role": "system", "content": profile.question_system},
        {"role": "user", "content": profile.question_rules + "\n\n" + regen_rules + "\n" + user_ctx},
    ]
