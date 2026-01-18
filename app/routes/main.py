
# this file consists of all the pipeline routes (all the API endpoints )

from flask import Flask, request, jsonify
from pydantic import ValidationError


from agents.models import UserInput
from agents.validation_utils import format_response
from services.fallback import get_fallback_state

app = Flask(__name__)

@app.route('/health', methods = ['GET'])
def health():
    return jsonify({"status": "ok"}), 200

# gets the user input , validates it , calls AI pipeline, formats response and returns questions
@app.route('/pipeline/run', methods=['POST'])
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
        # Mock pipeline call - replace with actual AI pipeline

        # For now, return mock response
        state = {
            "final_questions_by_beat": {},
            "pii_spans": [],
            "beat_plan": [],
            "audit_timeline": [],
            "validation_report": None
        }
        
        # Check if pipeline returned empty questions - use fallback
        if not state.get("final_questions_by_beat"):
            state = get_fallback_state()
            
    except Exception as e:
        # Pipeline failed - use fallback questions
        state = get_fallback_state()
    
    # format response for frontend
    response = format_response(state)
    
    # return JSON response
    return jsonify(response), 200

