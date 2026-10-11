"""QPU: submit baseline Estimator job + NoiseLearnerV3 job (only if not already saved)."""
exec(open("prep.py").read())
from qiskit_ibm_runtime import EstimatorV2 as Estimator
from qiskit_ibm_runtime.noise_learner_v3 import NoiseLearnerV3

jobs = load_jobs()
if "baseline" not in jobs:
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    c_isa = pm.run(circuit)
    est = Estimator(mode=backend)
    est.options.resilience_level = 0
    est.options.default_shots = 10_000
    j = est.run([(c_isa, observable.apply_layout(c_isa.layout))])
    save_job("baseline", j.job_id()); print("baseline job:", j.job_id())

NOISE_LEARNER_OPTIONS = {
    "num_randomizations": 32,
    "shots_per_randomization": 128,
    "layer_pair_depths": [1, 4, 16, 32],
    "post_selection": {"enable": True, "strategy": "edge", "x_pulse_type": "rx"},
}
if "noise_learning" not in jobs:
    j = NoiseLearnerV3(mode=backend, options=NOISE_LEARNER_OPTIONS).run(uniq["fwd"])
    save_job("noise_learning", j.job_id()); print("noise learning job:", j.job_id())
