# this file consists of all the pipeline routes (all the API endpoints )

from flask import Flask, request, jsonify, render_template
from pydantic import ValidationError
from typing import Any

from econf.env import get_env
from agents.models import UserInput
from agents.validation_utils import format_response
from agents.workflow import run_pipeline

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/pipeline/run", methods=["GET", "POST"])
def generate_questions():
    # --- GET: show demo page with sample data ---
    if request.method == "GET":
        data = {
            "scholarship_name": "Foresters Financial community grant",
            # IMPORTANT: must match your UserInput Literal options exactly
            "program_type": "Community Leadership",  # <- adjust to your enum
            "goal_one_liner": "Machine Learning Workshop hosts for academic engagement.",
            "resume_points": [
                "Led a team of 5 in developing a 3D CNN to decode emotional state from 7T fMRI brain images; improved test accuracy to 80%.",
                "Organized and hosted weekly paper reading groups for 15+ students on transformers.",
                "Conducted research under a professor, resulting in a published paper at NeurIPS 2025.",
            ],
        }
    else:
        data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "No JSON data provided",
            "error_type": "validation_error"
        }), 400

    try:
        user_input = UserInput.model_validate(data)
        out = run_pipeline(user_input)
        response = format_response(out)

        return render_template("index.html", data=response), 200

    except ValidationError as e:
        return jsonify({
            "error": "Invalid input",
            "error_type": "validation_error",
            "details": e.errors()
        }), 400

    except Exception as e:
        return jsonify({
            "error": "Pipeline failed",
            "error_type": "internal_error",
            "details": str(e),
        }), 500

if __name__ == "__main__":
    port = get_env("PORT")
    app.run(host="0.0.0.0", port=port, debug=True)
