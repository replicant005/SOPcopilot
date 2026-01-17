"""
Stores all the data models used by each agent.
"""

from typing import Optional, Literal, List
from typing_extensions import TypedDict, Annotated
from pydantic import BaseModel, Field
from operator import add

Beat = Literal["A", "B", "C", "D", "E"]

class UserInput(BaseModel) :
    scholarship_name: str = Field(...,
                                  min_length=1,
                                  max_length=200,
                                  description= "Name of the scholarship"
                                  )

    program_type: Literal["Undergrad", "Graduate",
                          "Research","Community Grant",
                          "PhD"] = Field(...,description="Type of program")

    goal_one_liner:str = Field(
        ...,
        min_length=10,
        max_length=500,
        description= "One sentence goal or story"
    )
    resume_points : list[str] = Field(
        ...,
        min_length=2,
        description="list of resume bullet points"
    )



class PiiSpan(BaseModel):
    start: int
    end: int
    pii_type: str
    confidence: Optional[float] = None


class BeatPlanItem(BaseModel):
    beat: Beat
    missing: list[str]
    guidance: Optional[str] = None


class QuestionObject(BaseModel):
    beat: Beat
    question: str
    intent: str
    
class BeatPlanOut(BaseModel):
    items: list[BeatPlanItem]

class QuestionsOut(BaseModel):
    items: list[QuestionObject]

class ValidationReport(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    repairs_applied: list[str] = Field(default_factory=list)


def merge_questions_by_beat(left: dict[Beat, List[QuestionObject]], right: dict[Beat, List[QuestionObject]]):
    out = dict(left or {})
    for beat, qs in (right or {}).items():
        out.setdefault(beat, []).extend(qs)
    return out

class PipelineState(TypedDict, total=False):
    # Inputs
    user_input: UserInput

    # Governance front gate
    canonical_input: str
    pii_spans: list[PiiSpan]
    redacted_input: str

    # Planning
    beat_plan: list[BeatPlanItem]

    # Map outputs (per beat)
    
    questions_by_beat: Annotated[dict[Beat, list[QuestionObject]], merge_questions_by_beat]

    # Reduce outputs
    final_questions_by_beat: dict[Beat, list[QuestionObject]]
    
    # Validation outputs
    failed_beats: list[Beat]
    failed_reasons: dict[Beat, list[str]]

    # Repair loop
    validation_report: ValidationReport
    attempt_count: int
    
    # user-side regen request
    regen_request: list[Beat]

    # communications
    # Note that I use Annotated here to ensure
    # concurrent workers do not overwrite each other.
    audit_log: Annotated[list[dict], add]
