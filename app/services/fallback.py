"""
Fallback service for when AI agents fail.
Provides generic questions organized by beat (A, B, C, D, E).
"""

from typing import Literal

Beat = Literal["A", "B", "C", "D", "E"]


def get_fallback_questions() -> dict[Beat, list[dict]]:
    """
    Returns generic fallback questions for each beat when AI pipeline fails.
    
    Returns:
        dict: Dictionary with beat keys (A-E) and lists of question dictionaries.
              Each question dict has: beat, question, intent
    """
    return {
        "A": [
            {
                "beat": "A",
                "question": "What motivated you to pursue this scholarship opportunity?",
                "intent": "Understand personal motivation and alignment with scholarship goals"
            },
            {
                "beat": "A",
                "question": "How does this scholarship align with your academic and career objectives?",
                "intent": "Assess goal clarity and scholarship fit"
            }
        ],
        "B": [
            {
                "beat": "B",
                "question": "Describe a significant challenge you have overcome and what you learned from it.",
                "intent": "Evaluate resilience and growth mindset"
            },
            {
                "beat": "B",
                "question": "What experiences have shaped your character and prepared you for this opportunity?",
                "intent": "Understand personal development and readiness"
            }
        ],
        "C": [
            {
                "beat": "C",
                "question": "How have you demonstrated leadership or initiative in your academic or community work?",
                "intent": "Assess leadership qualities and proactive engagement"
            },
            {
                "beat": "C",
                "question": "What specific contributions have you made to your field or community?",
                "intent": "Evaluate impact and meaningful engagement"
            }
        ],
        "D": [
            {
                "beat": "D",
                "question": "What are your short-term and long-term goals, and how will this scholarship help you achieve them?",
                "intent": "Understand goal clarity and scholarship impact"
            },
            {
                "beat": "D",
                "question": "How do you plan to use the knowledge and opportunities from this scholarship?",
                "intent": "Assess forward-thinking and application of benefits"
            }
        ],
        "E": [
            {
                "beat": "E",
                "question": "What unique perspectives or experiences do you bring that would enrich this program?",
                "intent": "Identify unique value and diversity of thought"
            },
            {
                "beat": "E",
                "question": "How will you contribute to the scholarship community and give back?",
                "intent": "Evaluate commitment to community and reciprocity"
            }
        ]
    }


def get_fallback_state() -> dict:
    """
    Returns a complete fallback state dictionary matching PipelineState structure.
    Used when AI pipeline fails completely.
    
    Returns:
        dict: Fallback state with generic questions and empty/default values for other fields
    """
    return {
        "final_questions_by_beat": get_fallback_questions(),
        "pii_spans": [],
        "redacted_input": "",
        "canonical_input": "",
        "beat_plan": [],
        "questions_by_beat": get_fallback_questions(),
        "validation_report": {
            "ok": False,
            "errors": ["AI pipeline failed - using fallback questions"],
            "warnings": [],
            "repairs_applied": []
        },
        "audit_timeline": [],
        "fallback_used": True
    }
