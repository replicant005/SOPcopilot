# this file consists of all the pipeline routes (all the API endpoints )

from flask import Flask, request, jsonify, render_template, stream_with_context, Response
from pydantic import ValidationError
from typing import Any
from json import dumps

from econf.env import get_env
from agents.models import UserInput
from agents.validation_utils import format_response
from agents.workflow import run_pipeline, GRAPH

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.post("/api/pipeline/run_stream")
def run_stream():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON data provided."}), 400
    
    try:
        user_input= UserInput.model_validate(data)
    except ValidationError as e:
        return jsonify({"error": "Invalid input", "details": e.errors()}), 400

    init_state = {
        "user_input": user_input,
        "attempt_count": 0,
        "questions_by_beat": {},
        "regen_request": [],
        "audit_log": [],
    }
    
    def ndjson(obj):
        return dumps(obj, ensure_ascii=False) + "\n"
    
    @stream_with_context
    def gen():
        final_state = None
        for st in GRAPH.stream(init_state, stream_mode="values"):
            final_state = st
            # If you also want updates, you can still emit a lightweight status event here
            # or switch to stream_mode="updates" and separately keep state via a checkpointer.
            yield ndjson({"type": "update", "data": {"state_keys": list(st.keys())}})
        yield ndjson({"type": "result", "data": format_response(final_state)})        
    return Response(gen(), mimetype="application/x-ndjson")
            

if __name__ == "__main__":
    port = get_env("PORT")
    app.run(host="0.0.0.0", port=port, debug=True)
