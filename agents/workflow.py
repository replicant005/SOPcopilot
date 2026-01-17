from agents.models import *
from agents.config import *
from agents.validation_utils import (
    _norm_q,
    _norm,
    _validate_question_text,
    _ungrounded_entities,
    _ungrounded_numbers,
)
from agents.prompts import beat_planner_messages, question_generator_messages
from econf.env import _set_env

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Any, Literal
from langchain_cohere import ChatCohere
from langgraph.types import Command, Send
from langgraph.graph import START, END, StateGraph
import re
from textwrap import dedent


_set_env("COHERE_API_KEY")
llm = ChatCohere(model="command-a-03-2025")


def _build_canonical_input(user_input: UserInput) -> str:
    """
    A helper to combine all the inputs together."""
    bullets = "\n".join(f"- {b}" for b in user_input.resume_points)
    return (
        f"Scholarship: {user_input.scholarship_name}\n"
        f"Program type: {user_input.program_type}\n"
        f"Goal: {user_input.goal_one_liner}\n"
        f"Resume points:\n{bullets}\n"
    )


def make_redactor_node(
    *,
    language: str = "en",
    entities: list[str] | None = None,
    default_operator: str = "replace",
):
    """
    A presidio wrapper to create the redactor node.
    """
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    entities = entities or [
        "PERSON",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "LOCATION",
        "CREDIT_CARD",
        "URL",
    ]

    # Replace PII with its entity type,<EMAIL_ADDRESS>.
    # (Presidio supports different operators; replace/mask/redact, etc.) :contentReference[oaicite:4]{index=4}
    operators: dict[str, OperatorConfig] = {
        "DEFAULT": OperatorConfig(default_operator, {"new_value": "<REDACTED>"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
        "PERSON": OperatorConfig("replace", {"new_value": "<NAME>"}),
        "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
        "URL": OperatorConfig("replace", {"new_value": "<URL>"}),
    }

    def redactor_node(state: "PipelineState") -> dict[str, Any]:
        user_input = state["user_input"]
        canonical = _build_canonical_input(user_input)

        results = analyzer.analyze(
            text=canonical,
            language=language,
            entities=entities,
        )

        pii_spans = [
            PiiSpan(
                start=r.start,
                end=r.end,
                pii_type=r.entity_type,
                confidence=float(r.score) if r.score is not None else None,
            )
            for r in results
        ]

        redacted = anonymizer.anonymize(
            text=canonical,
            analyzer_results=results,
            operators=operators,
        ).text

        return {
            "canonical_input": canonical,
            "pii_spans": pii_spans,
            "redacted_input": redacted,
            "attempt_count": state.get("attempt_count", 0),
            "questions_by_beat": state.get("questions_by_beat", {}),
        }

    return redactor_node


def beat_planner_node(state: PipelineState) -> Command[Literal["question_generator"]]:
    """
    Produces a list of beat plan item and sends a map task.
    """

    redacted_input = state["redacted_input"]

    planner = llm.bind(temperature=PLANNER_TEMP).with_structured_output(BeatPlanOut)
    out: BeatPlanOut = planner.invoke(beat_planner_messages(redacted_input))

    beat_plan = out.items

    # Hard enforcement: A–E exactly once
    beats = [b.beat for b in beat_plan]
    if sorted(beats) != ["A", "B", "C", "D", "E"]:
        raise ValueError(f"BeatPlanner must output A–E exactly once. Got: {beats}")

    sends = [
        Send(
            "question_generator",
            {
                "beat_task": item.model_dump(),
                "redacted_input": redacted_input,
            },
        )
        for item in beat_plan
    ]

    return Command(update={"beat_plan": beat_plan}, goto=sends)


def question_generator_node(
    task: BeatPlanItem, redacted_input: str
) -> list[QuestionObject]:
    """
    StateGraph node to generate questions.
    """
    generator = llm.bind(temperature=GENERATOR_TEMP).with_structured_output(
        QuestionsOut
    )
    out = generator.invoke(question_generator_messages(task, redacted_input))
    return out.items


def question_generator_worker(worker_state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate questions per beat.
    """

    if "beat_task" not in worker_state:
        raise KeyError(
            f"question_generator got keys: {list(worker_state.keys())}"
            f"Payload preview: {str(worker_state)}"
        )

    task = BeatPlanItem.model_validate(worker_state["beat_task"])
    redacted_input = worker_state["redacted_input"]

    questions = question_generator_node(task, redacted_input)

    return {"questions_by_beat": {task.beat: questions}}


def assembler_node(state: PipelineState) -> dict:
    """
    Deterministic "reduce": merge + dedupe + trim.
    Returns {"final_questions_by_beat": dict[Beat, list[QuestionObject]]}
    """
    questions_by_beat: dict[Beat, list[QuestionObject]] = (
        state.get("questions_by_beat", {}) or {}
    )

    # Ensure all beats exist
    merged: dict[Beat, list[QuestionObject]] = {b: [] for b in ALL_BEATS}
    for beat, qs in questions_by_beat.items():
        if beat in merged and qs:
            merged[beat].extend(qs)

    seen: set[str] = set()
    final_by_beat: dict[Beat, list[QuestionObject]] = {b: [] for b in ALL_BEATS}

    for beat in ALL_BEATS:
        for q in merged[beat]:
            if not q or not q.question:
                continue
            key = _norm_q(q.question)
            if key in seen:
                continue
            seen.add(key)
            final_by_beat[beat].append(q)

        if len(final_by_beat[beat]) > MAX_PER_BEAT:
            final_by_beat[beat] = final_by_beat[beat][:MAX_PER_BEAT]

    return {"final_questions_by_beat": final_by_beat}


def clear_failed_beats_questions(
    questions_by_beat: dict[Beat, list[QuestionObject]], failed_beats: list[Beat]
) -> dict[Beat, list[QuestionObject]]:
    qb = dict(questions_by_beat or {})
    for b in failed_beats:
        qb[b] = []
    return qb


def regenerate_questions(
    failed_beats: list[str], plan_map: dict[Beat, BeatPlanItem], redacted_input: str
) -> list[Send]:
    sends = []
    for b in failed_beats:
        bp = plan_map.get(b) or BeatPlanItem(beat=b, missing=[], guidance=None)

        # Strengthen guidance for regen (without relying on raw input)
        extra = dedent(
            "Regenerate questions. Do not introduce any new names, numbers, organizations, dates, or places, unless they appear verbatim in the provided redacted input."
        )
        new_guidance = (bp.guidance or "").strip()
        new_guidance = (new_guidance + " " + extra).strip()

        regen_task = BeatPlanItem(
            beat=bp.beat,
            missing=bp.missing,
            guidance=new_guidance,
        )

        sends.append(
            Send(
                "question_generator",
                {
                    "beat_task": regen_task.model_dump(),
                    "redacted_input": redacted_input,
                },
            )
        )
    return sends


def validator_node(state: PipelineState) -> Command | dict:
    # Placeholder for validation logic
    # return {"validation_report": ValidationReport(ok=True)}

    # Real implementations
    try:
        source_text = state["redacted_input"]
        source_norm = _norm(source_text)
        final_by_beat = state.get("final_questions_by_beat", {})

        failed_reasons: dict[Beat, list[str]] = {}
        failed_beats: list[Beat] = []
        for beat in ALL_BEATS:
            reasons = []
            qs = final_by_beat.get(beat, [])
            if not qs:
                reasons.append("Missing questions for this beat.")
            else:
                for qo in qs:
                    qtext = (qo.question or "").strip()
                    reasons.extend(_validate_question_text(qtext))
                    intent = (qo.intent or "").strip()
                    if not intent:
                        reasons.append("Missing intent.")
                    missing_nums = _ungrounded_numbers(qtext, source_norm)
                    if missing_nums:
                        reasons.append(
                            f"Ungrounded numbers not found in source: {missing_nums}"
                        )

                    missing_entities = _ungrounded_entities(
                        qtext, source_text, source_norm
                    )
                    if missing_entities:
                        reasons.append(
                            f"Ungrounded entities not found in source: {missing_entities}"
                        )

                    if "@" in qtext:
                        reasons.append("Email-like token detected in question.")
                    if re.search(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b", qtext):
                        reasons.append("Phone-like token detected in question.")

            if reasons:
                failed_reasons[beat] = sorted(set(reasons))
                failed_beats.append(beat)

        ok = len(failed_beats) == 0
        report = ValidationReport(
            ok=ok,
            errors=[f"{b}: {failed_reasons[b]}" for b in failed_beats],
            warnings=[],
            repairs_applied=[],
        )

        if ok:
            return Command(update={"validation_report": report}, goto=END)

        attempt = int(state.get("attempt_count") or 0) + 1
        report.repairs_applied.append(
            f"Attempt {attempt}: regenerate beats {failed_beats}"
        )

        if attempt >= MAX_ATTEMPT:
            report.warnings.append(
                "Max repair attempts reached; returning best-effort output."
            )
            report.ok = True
            return Command(
                update={"validation_report": report, "attempt_count": attempt}, goto=END
            )

        qb = state.get("questions_by_beat", {}) or {}
        qb_cleared = clear_failed_beats_questions(qb, failed_beats)

        # Create regen sends
        beat_plan = state.get("beat_plan", []) or []
        plan_map = {bp.beat: bp for bp in beat_plan}

        sends = regenerate_questions(failed_beats, plan_map, redacted_input=source_text)

        return Command(
            update={
                "validation_report": report,
                "attempt_count": attempt,
                "failed_beats": failed_beats,
                "failed_reasons": failed_reasons,
                "questions_by_beat": qb_cleared,
            },
            goto=sends,
        )
    except Exception as e:
        print(f"The following error occured: {e}")


def create_graph():
    builder = StateGraph(PipelineState)

    builder.add_node("redactor", make_redactor_node())
    builder.add_node("beat_planner", beat_planner_node)
    builder.add_node("question_generator", question_generator_worker)
    builder.add_node("assembler", assembler_node)
    builder.add_node("validator", validator_node)

    builder.add_edge(START, "redactor")
    builder.add_edge("redactor", "beat_planner")

    builder.add_edge("question_generator", "assembler")
    builder.add_edge("assembler", "validator")
    builder.add_edge("validator", END)

    graph = builder.compile()
    return graph


def run_pipeline(user_input: UserInput) -> dict[Beat, list[QuestionObject]]:
    """
    Exapmle of an user input:
    exp1 = {
    "scholarship_name": "Vector scholarships",
    "program_type": "Community Leadership",
    "goal_one_liner": "Machine Learning Workshop hosts for academic engagement.",
    "resume_points": [
        "Led a team of 5 in developing a 3D CNN to decode emotional state from 7tfMRI brain images, improved the test accuracy to 80%."
        "Organized and hosted weekly study paper reading groups for over 15 students in transformers.",
        "Conducted research under Prof Geoffery Hinton, resulting in a published paper in a Neurlps 2025 conference.",
        ],
    }
    """

    try:
        graph = create_graph()
        out = graph.invoke({"user_input": user_input})
        return out
    except Exception as e:
        print(f"Exception occured due to {type(e)} as follows | {e}.")
