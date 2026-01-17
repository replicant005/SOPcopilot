from agents.workflow import run_pipeline
from agents.models import UserInput

from pprint import pprint

exp1 = {
    "scholarship_name": "Vector scholarships",
    "program_type": "Graduate",
    "goal_one_liner": "Machine Learning Workshop hosts for academic engagement.",
    "resume_points": [
        "Led a team of 5 in developing a 3D CNN to decode emotional state from 7tfMRI brain images, improved the test accuracy to 80%."
        "Organized and hosted weekly study paper reading groups for over 15 students in transformers.",
        "Conducted research under Prof Geoffery Hinton, resulting in a published paper in a Neurlps 2025 conference.",
    ],
}


exp2 = {
    "scholarship_name": "Foresters Financial community grant",
    "program_type": "Community Grant",
    "goal_one_liner": "Machine Learning Workshop hosts for academic engagement.",
    "resume_points": [
        "Led a team of 5 in developing a 3D CNN to decode emotional state from 7tfMRI brain images, improved the test accuracy to 80%."
        "Organized and hosted weekly study paper reading groups for over 15 students in transformers.",
        "Conducted research under Prof Geoffery Hinton, resulting in a published paper in a Neurlps 2025 conference.",
    ],
}


user_input = UserInput.model_validate(exp2)
out = run_pipeline(user_input)

pprint(out, indent=2)
