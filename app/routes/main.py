# this file consists of all the pipeline routes (all the API endpoints )

from flask import Blueprint, request, jsonify
from pydantic import ValidationError, BaseModel
from typing import Union

# pydantic schema for input validation
from app.schemas.request import UserInput
# create a bueprint for group related routes 
bp = Blueprint('main', __name__)

# to ckeck if flask is running 
@bp.route('/health', methods = ['GET'])
def health():
    return jsonify({"status": "ok"}), 200


# gets the user input , validates it , calls AI pipeline, formats response and returns questions
@bp.route('/pipeline/run', methods=['POST'])
def run_pipeline():
    # receive and parse JSON request
    data = request.get_json()
    
    # check if request has data
    if not data:
        return jsonify({
            "error": "No JSON data provided",
            "error_type": "validation_error"
        }), 400
    
    # validate input with Pydantic
    try:
        user_input = UserInput.model_validate(data)
    except ValidationError as e:
        # Pydantic validation failed - return 400 with details
        return jsonify({
            "error": "Invalid input",
            "error_type": "validation_error",
            "details": e.errors()  # List of validation errors
        }), 400
    
    # call AI pipeline (replace with actual import)
    # TODO: import AI pipoline here 
    try:
        state = {
            "final_questions_by_beat": {},
            "pii_spans": [],
            "beat_plan": [],
            "audit_timeline": [],
            "validation_report": None
        }
        #TODO : activate the fall back here 
    except Exception as e:
        return jsonify({
            "error": "Pipeline execution failed",
            "error_type": "pipeline_error",
            "details": str(e) if request.app.config['DEBUG'] else None
        }), 500
    
    # format response for frontend
    response = format_response(state)
    
    # return JSON response
    return jsonify(response), 200

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