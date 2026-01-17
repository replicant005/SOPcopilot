"""
Core validation logic that checks:

1. Coverage (A-E present)
2. Question formatting (single-line, ends with ?)
3. Intent length sanity
4. No PII placeholders
5. Ungrounded numbers (any numbers in question must appear in the redacted input)
6. Ungrounded name entities using spaCy NER. It must apear in redacted_input.
e.g. Institution name, research subdomains, research roles...
"""

import re
try:
    from spacy import load
    NER_MODEL = load("en_core_web_sm", disable=["parser", "lemmatizer"])
except Exception:
    NER_MODEL = None

from typing import Union
from pydantic import BaseModel
    
_num_re = re.compile(r"\b\d+(\.\d+)?%?\b")
_placeholder_re = re.compile(r"<(NAME|EMAIL|PHONE|LOCATION|URL|REDACTED)>", re.IGNORECASE)

def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _norm_q(s: str) -> str:
    # Normalize for dedupe: lowercase, collapse whitespace, strip punctuation-ish
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[“”\"'`]", "", s)
    s = re.sub(r"\s*\?\s*$", "?", s)  # unify question mark ending
    return s

def _ungrounded_numbers(question: str, source_norm: str) -> list[str]:
    nums = {m.group(0) for m in _num_re.finditer(question)}
    missing = []
    for n in nums:
        n_norm = _norm(n)
        if n_norm not in source_norm:
            missing.append(n)
    return sorted(set(missing))

def _ungrounded_entities(question: str, source_text: str, source_norm: str) -> list[str]:
    if NER_MODEL is not None:
        doc = NER_MODEL(question)
        suspects = []
        for ent in doc.ents:
            if ent.label_ in {"PERSON", "ORG", "GPE", "LOC", "DATE", "TIME", "MONEY", "PERCENT", "EVENT", "PRODUCT"}:
                ent_text = ent.text.strip()
                if len(ent_text) < 2:
                    continue
                # Compare normalized versions
                if _norm(ent_text) not in source_norm:
                    suspects.append(ent_text)
        return sorted(set(suspects))

    # Deterministic fallback.
    props = re.findall(r"\b[A-Z][a-zA-Z]+\b", question)
    suspects = []
    for p in props:
        if _norm(p) not in source_norm:
            suspects.append(p)
    return sorted(set(suspects))

def _validate_question_text(q: str) -> list[str]:
    reasons = []
    if not q.strip():
        reasons.append("Empty question text.")
        return reasons
    if "\n" in q.strip():
        reasons.append("Question must be single-line.")
    if not q.strip().endswith("?"):
        reasons.append("Questions must end with '?'.")
    if q.strip().startswith(("1)", "2)", "-", "*")):
        reasons.append("Looks like a list item, not a standalone question.")
    if _placeholder_re.search(q):
        reasons.append("Question references redaction placeholders (e.g., <NAME>).")
    return reasons

#  function to format the response 
# args being the pydantic model from the pipeline and the result will be a JSON 
# union is basically specifying thta state cam either be a dict or a base model 
# so the function accepts -  a pydantic model or dict
def format_response(state: Union[dict, BaseModel]) -> dict:
    # Convert Pydantic model state to dict if needed

    if hasattr(state, 'model_dump'):
        # Pydantic model - convert to dict
        state_dict = state.model_dump()
    else:
        # Already a dict
        state_dict = state
    
    # walks through any structure and cleans it (converst into dict)
    def to_dict(obj):
        if hasattr(obj, 'model_dump'):
            # Pydantic model - convert to dict
            return obj.model_dump()
        elif isinstance(obj, dict):
            # Dict - recursively convert values
            return {k: to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # List - recursively convert items
            return [to_dict(item) for item in obj]
        else:
            # Primitive type - return as-is
            return obj
    
    # Format response structure
    formatted = {
        # Final output (what frontend displays)
        "final_questions_by_beat": to_dict(
            state_dict.get("final_questions_by_beat", {})
        ),
        
        # Redactor Agent output (for PII highlights panel)
        "pii_spans": to_dict(state_dict.get("pii_spans", [])),
        "redacted_input": state_dict.get("redacted_input", ""),
        "canonical_input": state_dict.get("canonical_input", ""),
        
        # Beat Planner Agent output (for beat plan panel)
        "beat_plan": to_dict(state_dict.get("beat_plan", [])),
        
        # Question Generator outputs (intermediate, before assembly)
        "questions_by_beat": to_dict(state_dict.get("questions_by_beat", {})),
        
        # Validator Agent output (for validation panel)
        "validation_report": to_dict(state_dict.get("validation_report")),
        
        # Audit timeline (for progress panel)
        "audit_timeline": state_dict.get("audit_timeline", []),
        
        # Metadata
        "fallback_used": state_dict.get("fallback_used", False),
    }
    
    return formatted