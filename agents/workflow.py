from agents.models import *
from agents.config import *
from agents.validation_utils import (
    _norm_q,
    _norm,
    _validate_question_text,
    _ungrounded_entities,
    _ungrounded_numbers,
)
# from agents.prompts import beat_planner_messages, question_generator_messages
from agents.prompts import beat_planner_messages, question_generator_messages
from agents.logger_utils import log_event, log_event_patch
from econf.env import _set_env

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Any, Literal
from textwrap import dedent
from time import perf_counter
from langchain_cohere import ChatCohere
from langgraph.types import Command, Send
from langgraph.graph import START, END, StateGraph
import re


_set_env("COHERE_API_KEY")
llm = ChatCohere(model="command-a-03-2025")
 

def _build_canonical_input(user_input: UserInput) -> str:
    """
    A helper to combine all the inputs together."""
    bullets = "\n".join(f"- {b}" for b in user_input.resume_points)
    return (
        f"Scholarship: {user_input.scholarship_name}\n"
        f"Scholarship type: {user_input.program_type}\n"
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
        t0 = perf_counter()
        user_input = state["user_input"]
        canonical = _build_canonical_input(user_input)

        start_patch = log_event(state, "redactor", "start", {"len_canonical": len(canonical)})

        results = analyzer.analyze(text=canonical, language=language, entities=entities)

        pii_spans = [
            PiiSpan(
                start=r.start, end=r.end, pii_type=r.entity_type,
                confidence=float(r.score) if r.score is not None else None,
            )
            for r in results
        ]

        redacted = anonymizer.anonymize(
            text=canonical, analyzer_results=results, operators=operators
        ).text

        dt_ms = (perf_counter() - t0) * 1000
        end_patch = log_event(
            state, "redactor", "end",
            {"pii_count": len(pii_spans), "latency_ms": round(dt_ms, 2)}
        )

        return {
            "canonical_input": canonical,
            "pii_spans": pii_spans,
            "redacted_input": redacted,
            "attempt_count": state.get("attempt_count", 0),
            "questions_by_beat": state.get("questions_by_beat", {}),
            **start_patch,
            **end_patch,
        }

    return redactor_node


def beat_planner_node(state: PipelineState) -> Command[Literal["question_generator"]]:
    """
    Produces a list of beat plan item and sends a map task.
    """
    program_type = state["user_input"].program_type
    redacted_input = state["redacted_input"]

    planner = llm.bind(temperature=PLANNER_TEMP).with_structured_output(BeatPlanOut)
    out = planner.invoke(beat_planner_messages(program_type, redacted_input))

    beat_plan = out.items

    # Hard enforcement: A–E exactly once
    beats = [b.beat for b in beat_plan]
    if sorted(beats) != ["A", "B", "C", "D", "E"]:
        raise ValueError(f"BeatPlanner must output A–E exactly once. Got: {beats}")

    sends = [
        Send("question_generator", {
                "beat_task": item.model_dump(),
                "redacted_input": redacted_input,
                "program_type": program_type,
            })
        for item in beat_plan
    ]
    
    
    log_patch = log_event(
        state, 
        "beat_planner", 
        "created_beat_plan", 
        {"beats": [x.beat for x in beat_plan],
         "missing_counts": {x.beat: len(x.missing)  for x in beat_plan},}
        )
    return Command(update={"beat_plan": beat_plan, **log_patch}, goto=sends)

def question_generator_node(task: BeatPlanItem, 
                            program_type: str, 
                            redacted_input: str
                            ) -> list[QuestionObject]:
    """
    StateGraph node to generate questions.
    """
    try:
        generator = llm.bind(temperature=GENERATOR_TEMP).with_structured_output(QuestionsOut)
        out = generator.invoke(
            question_generator_messages(
                task, 
                program_type,
                redacted_input
                ))
        return out.items
    except Exception as e:
        raise Exception(f"Unexpected exception: {e}")


def question_generator_worker(worker_state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate questions per beat (map worker).
    Emits audit_log patches that will merge into shared state.
    """
    t0 = perf_counter()

    # Defensive: record keys early (super useful in debugging)
    start_patch = log_event_patch(
        agent="question_generator",
        event="start",
        data={"keys": list(worker_state.keys())},
    )

    try:
        task = BeatPlanItem.model_validate(worker_state["beat_task"])
        program_type = worker_state["program_type"]
        redacted_input = worker_state["redacted_input"]

        questions = question_generator_node(task, program_type, redacted_input)

        dt_ms = (perf_counter() - t0) * 1000
        ok_patch = log_event_patch(
            agent="question_generator",
            event="success",
            data={
                "beat": task.beat,
                "n_questions": len(questions),
                "latency_ms": round(dt_ms, 2),
            },
        )

        return {
            **start_patch,
            **ok_patch,
            "questions_by_beat": {task.beat: questions},
        }

    except KeyError:
        dt_ms = (perf_counter() - t0) * 1000
        err_patch = log_event_patch(
            agent="question_generator",
            event="error",
            data={
                "error_type": "KeyError",
                "worker_state_keys": list(worker_state.keys()),
                "latency_ms": round(dt_ms, 2),
            },
        )
        # keep raising, but still return patch if you prefer “best-effort”
        raise Exception(
            f"Key error occurred during question generation. worker_state keys={list(worker_state.keys())}"
        ) from None

    except Exception as e:
        dt_ms = (perf_counter() - t0) * 1000
        _ = log_event_patch(
            agent="question_generator",
            event="error",
            data={
                "error_type": type(e).__name__,
                "message": str(e),
                "latency_ms": round(dt_ms, 2),
            },
        )
        raise Exception(f"Unexpected exception: {e}.") from e

def assembler_node(state: PipelineState) -> dict:
    """
    Deterministic "reduce": merge + dedupe + trim.
    """
    questions_by_beat: dict[Beat, list[QuestionObject]] = (
        state.get("questions_by_beat", {}) or {}
    )

    # Ensure all beats exist
    merged: dict[Beat, list[QuestionObject]] = {b: [] for b in ALL_BEATS}
    for beat, qs in questions_by_beat.items():
        if beat in merged and qs:
            merged[beat].extend(qs)

    pre_merge_count = sum(len(v) for v in merged.values())

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
    
    post_merge_count = sum(len(v) for v in final_by_beat.values())
    

    beat_counts = {b: len(final_by_beat[b]) for b in ALL_BEATS}

    return {
        "final_questions_by_beat": final_by_beat,
        **log_event(state, "assembler", "reduce_complete", {
            "total_pre_dedupe": pre_merge_count,
            "total_post_dedupe": post_merge_count,
            "per_beat_counts": beat_counts,
        }),
    }

def clear_failed_beats_questions(
    questions_by_beat: dict[Beat, list[QuestionObject]], failed_beats: list[Beat]
) -> dict[Beat, list[QuestionObject]]:
    qb = dict(questions_by_beat or {})
    for b in failed_beats:
        qb[b] = []
    return qb


def regenerate_questions(failed_beats: list[str], 
                         plan_map: dict[Beat, BeatPlanItem], 
                         program_type: str,
                         redacted_input: str
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
                    "program_type": program_type,
                    "redacted_input": redacted_input,
                },
            )
        )
    return sends


def validator_node(state: PipelineState) -> Command | dict:
    """
    Core validation logic that checks:

    1. Coverage (A-E present)
    2. Question formatting (single-line, ends with ?)
    3. Intent length sanity
    4. No PII placeholders
    5. Ungrounded numbers (any numbers in question must appear in the redacted input)
    6. Ungrounded name entities using spaCy NER. It must apear in redacted_input.
    e.g. institution name, advisor's name, emails, etc...
    """
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
        
        base_log = log_event(
            state,
            "validator",
            "checked",
            {"ok": ok, "failed_beats": failed_beats, "num_failed_beats": len(failed_beats)}
        )

        if ok:
            return Command(update={"validation_report": report, **base_log}, goto=END)

        attempt = int(state.get("attempt_count") or 0) + 1
        report.repairs_applied.append(
            f"Attempt {attempt}: regenerate beats {failed_beats}"
        )
        
        repair_log = log_event(
            state,
            "validator",
            "repair_planned",
            {
                "attempt": attempt,
                "beats_to_regen": failed_beats,
            }
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
        program_type = state["user_input"].program_type

        sends = regenerate_questions(failed_beats, 
                                     plan_map, program_type=program_type,redacted_input=source_text)

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


GRAPH = create_graph()
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

    THEN write
    user_input = UserInput.model_validate(exp1)
    """

    try:
        out = GRAPH.invoke({"user_input": user_input})
        return out
    except Exception as e:
        print(f"Exception occured due to {type(e)} as follows | {e}.")
