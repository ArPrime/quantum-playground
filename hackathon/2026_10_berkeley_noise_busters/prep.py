"""CPU-only: backend, layout, transpile, box both circuits, find unique 2q layers."""
import pickle
from common import *
from qiskit.transpiler import generate_preset_pass_manager
from samplomatic.transpiler import generate_boxing_pass_manager
from samplomatic.utils import find_unique_box_instructions

service = get_service()
jobs = load_jobs()
if "backend" in jobs:
    name = jobs["backend"]
else:
    name = service.least_busy(operational=True, simulator=False,
        filters=lambda b: b.processor_type.get("family") == "Heron").name
    save_job("backend", name)
backend = service.backend(name, use_fractional_gates=True)
print("backend:", backend.name)

def measured(qc):
    c = qc.copy(); c.measure_active(); return c

layout_pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
layout = layout_pm.run(measured(circuit)).layout.final_index_layout()
isa_pm = generate_preset_pass_manager(backend=backend, initial_layout=layout, optimization_level=0)
isa = {"fwd": isa_pm.run(measured(circuit)), "mirror": isa_pm.run(measured(circuit_mirror))}
print("layout:", layout)

boxes_pm = generate_boxing_pass_manager(
    twirling_strategy="active",
    inject_noise_strategy="individual_modification",
    inject_noise_site="after",
    inject_noise_targets="gates",
    measure_annotations="all",
)
boxed = {k: boxes_pm.run(v) for k, v in isa.items()}
uniq = {k: find_unique_box_instructions(v, normalize_annotations=None, undress_boxes=True)
        for k, v in boxed.items()}
for k in boxed:
    nb = sum(1 for i in boxed[k].data if i.operation.name == "box")
    print(f"{k}: boxes={nb}, unique layers={len(uniq[k])}")
