# this file consists of all the pipeline routes (all the API endpoints )

from flask import Flask, request, jsonify, render_template, stream_with_context, Response
from pydantic import ValidationError
from typing import Any
from json import dumps

from econf.env import get_env
from agents.models import UserInput
from agents.validation_utils import format_response, create_custom_errors
from agents.workflow import GRAPH

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
        user_input = UserInput.model_validate(data)
    except ValidationError as e:
        # Return NDJSON 'error' event (so your streaming client shows a nice message)
        def gen_err(e):
            yield dumps({"type": "error", "error": "INPUT_VALIDATION", "data": create_custom_errors(e)}) + "\n"
        return Response(gen_err(e), mimetype="application/x-ndjson", status=400)

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
        audit_cursor = 0
        pii_sent = False

        def dump_pii(spans):
            out = []
            for s in (spans or []):
                if hasattr(s, "model_dump"):
                    out.append(s.model_dump())
                elif isinstance(s, dict):
                    out.append(s)
                else:
                    out.append({"start": getattr(s, "start", None),
                                "end": getattr(s, "end", None),
                                "pii_type": getattr(s, "pii_type", None),
                                "confidence": getattr(s, "confidence", None)})
            return out

        for st in GRAPH.stream(init_state, stream_mode="values"):
            final_state = st

            # 1) Stream PII spans once
            spans = st.get("pii_spans")
            if spans and not pii_sent:
                pii_sent = True
                yield ndjson({
                    "type": "update",
                    "data": {"pipeline": {"pii_spans": dump_pii(spans)}}
                })

            # 2) Stream audit log deltas
            audit = st.get("audit_log") or []
            new_events = audit[audit_cursor:]
            audit_cursor = len(audit)
            if new_events:
                yield ndjson({
                    "type": "update",
                    "data": {"pipeline": {"audit_log": new_events}}
                })

        yield ndjson({"type": "result", "data": format_response(final_state)})

    return Response(gen(), mimetype="application/x-ndjson")

if __name__ == "__main__":
    port = get_env("PORT")
    app.run(host="0.0.0.0", port=port, debug=True)
