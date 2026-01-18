from agents.workflow import run_pipeline
from agents.models import UserInput
from time import perf_counter

from pprint import pprint

start = perf_counter()

exp1 = UserInput(
  scholarship_name="UofT Summer Research Experience Award",
  program_type="Undergrad",
  goal_one_liner="I want to explore computer vision for medical imaging and learn how to do research with a lab team.",
  resume_points=[
    "Built a PyTorch object detector and evaluated mAP on a custom dataset",
    "Led a 4-person hackathon team; shipped a full-stack web app in 36 hours",
    "Tutored calculus and linear algebra; created weekly practice sets for 30+ students",
  ]
)

exp2 = UserInput(
  scholarship_name="NSERC CGS-M",
  program_type="Graduate",
  goal_one_liner="I want to research robust representation learning for scientific imaging, bridging physics intuition and deep learning.",
  resume_points=[
    "Trained contrastive models to learn embeddings from high-dimensional click probability data",
    "Implemented Faster R-CNN and YOLO pipelines; compared metrics and inference speed",
    "Wrote reproducible ML training scripts with deterministic seeds and artifact versioning",
  ]
)

out = run_pipeline(exp1)
end = perf_counter()
print("Exec time: ", end - start)

pprint(out, indent=2)
