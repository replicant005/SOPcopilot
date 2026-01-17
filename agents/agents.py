from models import *
from config import *
from prompts import beat_planner_messages, question_generator_messages

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Any, Literal
from langchain_cohere import ChatCohere
from langgraph.types import Command, Send
from langgraph.graph import START, END, StateGraph
import re

from os import environ
from getpass import getpass

def _set_env(var: str):
    if not environ.get(var):
        environ[var] = getpass(f"{var}: ")

_set_env("COHERE_API_KEY")

llm = ChatCohere(
    model="command-a-03-2025"
)

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
) :
    """
    A presidio wrapper to create the redactor node.
    """
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    entities = entities or ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "CREDIT_CARD", "URL"]

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

def _norm_q(s: str) -> str:
    # Normalize for dedupe: lowercase, collapse whitespace, strip punctuation-ish
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[“”\"'`]", "", s)
    s = re.sub(r"\s*\?\s*$", "?", s)  # unify question mark ending
    return s

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
        Send("question_generator", {
            "beat_task": item.model_dump(),
            "redacted_input": redacted_input,
        })
        for item in beat_plan
    ]

    return Command(update={"beat_plan": beat_plan}, goto=sends)


def question_generator_node(task: BeatPlanItem, redacted_input: str) -> list[QuestionObject]:
    """
    StateGraph node to generate questions.
    """ 
    generator = llm.bind(temperature=GENERATOR_TEMP).with_structured_output(QuestionsOut)
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
    questions_by_beat: dict[Beat, list[QuestionObject]] = state.get("questions_by_beat", {}) or {}

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
