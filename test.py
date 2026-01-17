from agents.workflow import run_pipeline
from agents.models import UserInput
from time import perf_counter

from pprint import pprint

exp1 = {
    "scholarship_name": "Vector scholarships",
    
    # Remember, it needs to be either one of ["Graduate", "Undergraduate", "Community Grant"]
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

start = perf_counter()
user_input = UserInput.model_validate(exp2)
out = run_pipeline(user_input)
end = perf_counter()
print("Exec time: ", end - start)

pprint(out, indent=2)
