from textwrap import dedent
from agents.models import BeatPlanItem, UserInput

from textwrap import dedent

def _program_slots(program_type: str) -> str:
    if program_type == "Graduate":
        return (
            "=== Program-Specific Context (Graduate) ===\n"
            "[Research Direction] \n"
            "[Target Lab/Faculty Fit] \n"
            "[Methods/Skills Readiness] \n"
        )
    if program_type == "Undergrad":
        return (
            "=== Program-Specific Context (Undergraduate) ===\n"
            "[Exploration Path] \n"
            "[Learning Plan] \n"
            "[Mentorship Style] \n"
        )
    if program_type == "Community Grant":
        return (
            "=== Program-Specific Context (Community Grant) ===\n"
            "[Community Need] \n"
            "[Stakeholders/Partners] \n"
            "[Success Metrics] \n"
            "[Sustainability Plan] \n"
        )
    return ""

def _build_canonical_input(user_input: UserInput) -> str:
    bullets = user_input.resume_points or []
    resume_block = "\n".join(f"[Resume Point #{i+1}] {b}" for i, b in enumerate(bullets)) or "[Resume Point #1] (none provided)"

    return (
        "=== Opportunity ===\n"
        f"[Scholarship Name] {user_input.scholarship_name}\n"
        f"[Program Type] {user_input.program_type}\n\n"
        "=== Applicant Goal ===\n"
        f"[Goal One-liner] {user_input.goal_one_liner}\n\n"
        f"{_program_slots(user_input.program_type)}\n"
        "=== Experience Inventory ===\n"
        f"{resume_block}\n"
    )

def _beat_defs(program_type: str) -> str:

    if program_type == "Community Grant":
        return dedent(
            """\
      Beats:
      A: Purpose & Fit
      B: Excellence / Proof
      C: Impact
      D: Leadership & Character
      E: Reflection & Growth
      """
        )
    elif program_type == "Graduate":
        return dedent(
            """\
      Beats:
      A: Purpose & Fit
      B: Excellence / Proof
      C: Impact
      D: Leadership & Character
      E: Reflection & Growth

      The opportunity the user indicated is linked to a graduate (masters/PhD) program.


      For example, the user may (a) be applying to a PhD (research) program and \
      (b) have research experience on their resume. Suppose you are working on beat A: Purpose & Fit. \
      In this case, you should output anchors to both the fact that the PhD is a research program and \
      their past experience in research. You may say that missing information includes the research \
      fit between the two, or the motivation the user has to commit to a research program.
      """
        )
    elif program_type == "Undergrad":
        return dedent(
            """
      Beats:
      A: Purpose & Fit
      B: Excellence / Proof
      C: Impact
      D: Leadership & Character
      E: Reflection & Growth

      The opportunity the user indicated is linked to an undergraduate (associate/bachelor) program.


      For example, the user may (a) be applying to a Research Experience for Undergraduates (REU) (research) program and \
      (b) have research experience on their resume. Suppose you are working on beat A: Purpose & Fit. \
      In this case, you should output anchors to both the fact that the REU is a research program and \
      their past experience in research. You may say that missing information includes the research \
      fit between the two, or the motivation the user has to commit to a research program.
        """
        )

    else:
        return dedent(
            f"""
    Beats:
      A: Purpose & Fit
      B: Excellence / Proof
      C: Impact
      D: Leadership & Character
      E: Reflection & Growth

      The opportunity the user indicated is linked to a program of type: {program_type}.

      When outputing anchors, missing, and so on, keep in mind considerations unique to programs of type: {program_type}.
    """
        )


def beat_planner_messages(program_type: str, redacted_input: str):

    system = dedent(
        """\
    You are a beat planner for a Statement of Purpose writing assistant. \
      A beat is a point or story to write around.
    The writing assistant generates questions based on the user's current writing, \
      inspired by the snowflake method of writing.
    Return structured data only. No prose.
    """
    )

    rules = dedent(
        """\
    Create a plan for beats A–E.

    For each beat, output:
    - beat: one of A,B,C,D,E.
    - missing: 2-4 short, specific missing details needed to write that beat, \
      grounded in the redacted input (reference the section name when possible).
    - guidance: one actionable hint (<= 20 words). Tailor this to the opportunity \
        listed in the redacted input. For example, if it is a scholarship for community service, \
        and asks for examples of community service\
    - anchors: 2-4 exact phrases copied verbatim from the redacted input (each <= 6 words) \
      that are relevant to this beat, along with where they appear.
    
    For example, the user may (a) be applying to a PhD (research) program and \
      (b) have research experience on their resume. Suppose you are working on beat A: Purpose & Fit. \
      In this case, for anchors, you should output anchors to the fact that the PhD is a research program and \
      that they have past experience in research. \
      For missing, You may include that missing information includes the research \
      fit between the two, or the motivation the user has to commit to a research program, or a specific \
      illustrative anecdote for a specific trait requested by admissions commit3tees, such as intelligence, \
      persistence, and so on. \
      For guidance, you may give a hint such as `
    """
    )

    user_ctx = dedent(
        f"""\
    {_beat_defs(program_type)}
    Redacted canonical input (source of truth):
    {redacted_input}

    Return a beat plan.
    """
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": rules + "\n\n" + user_ctx},
    ]


def question_generator_messages(
    task: BeatPlanItem, program_type: str, redacted_input: str
):
    system = dedent(
        """\
    You generate tailored questions to help an applicant write their Statement of Purpose.
    Return structured data only. No prose.
    """
    )

    regen_mode = bool(task.guidance and "Regenerate questions" in task.guidance)

    base_rules = dedent(
        """\
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
    """
    )

    grounding_rules = dedent(
        """\
    Grounding rules:
    - Do NOT introduce specific names, organizations, dates, locations, or numbers
      unless they appear verbatim in the provided redacted input.
    - If a specific detail is missing, ask for it instead of assuming it.
    """
    )

    anti_generic_rules = dedent(
        """\
    Anti-generic rules:
    - Each question must be anchored: it must include an exact short phrase from task.anchors
      (verbatim) OR explicitly reference a specific section/item from the redacted input
      (e.g., “Experience Inventory #2”).
    - Avoid generic openers like “Tell me about a time…” unless tied to a named anchor.
    - No filler: every question must point to a concrete story, decision, or evidence.
    """
    )

    regen_rules = (
        dedent(
            """\
    Regeneration rule:
    - Previous output failed validation. Make questions more grounded and less assumption-heavy.
    - Prefer asking for missing details rather than stating facts.
    """
        )
        if regen_mode
        else ""
    )

    beat_ctx = dedent(
        f"""\
    Beat: {task.beat}
    Missing: {task.missing}
    Guidance: {task.guidance}
    Anchors: {getattr(task, "anchors", [])}
    """
    )

    user = dedent(
        f"""\
    {_beat_defs(program_type)}
    {beat_ctx}

    Redacted input (source of truth):
    {redacted_input}
    """
    )

    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": base_rules
            + grounding_rules
            + anti_generic_rules
            + regen_rules
            + "\n\n"
            + user,
        },
    ]
