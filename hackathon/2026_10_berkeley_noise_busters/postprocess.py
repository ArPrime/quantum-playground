"""Post-process executor results into <Z6Z7> (raw, TREX-only, SLC+TREX+post-selection)."""
from common import *
import pickle, sys
from qiskit_addon_utils.exp_vals.expectation_values import executor_expectation_values
from qiskit_addon_utils.noise_management import trex_factors
from qiskit_addon_utils.noise_management.post_selection import PostSelector

service = get_service(); jobs = load_jobs()
backend = service.backend(jobs["backend"], use_fractional_gates=True)
nl = service.job(jobs["noise_learning"]).result()
meas_map = nl[-1].to_pauli_lindblad_map()
S = pickle.load(open("slc_state.pkl", "rb"))
out = {"baseline": float(service.job(jobs["baseline"]).result()[0].data.evs)}
for k in ["fwd", "mirror"]:
    r = service.job(jobs[f"executor_{k}"]).result()
    s = S[k]; trex = trex_factors(meas_map, s["rev"])
    ps = PostSelector.from_circuit(circuit=s["final_tmpl"], coupling_map=backend.coupling_map)
    def ev(d, gamma=1.0, mitigate=True, strat="node"):
        kw = dict(postselect_mask=ps.compute_mask(d, strategy=strat), rescale_factors=trex) if mitigate else {}
        v = executor_expectation_values(d["meas"], s["rev_meas"], None, avg_axis=0,
            measurement_flips=d["measurement_flips.meas"], pauli_signs=d.get("pauli_signs", None),
            gamma_factor=gamma, **kw)
        return float(v[0][0]), float(np.sqrt(v[0][1]))
    out[f"{k}_raw"] = ev(r[1], mitigate=False)
    out[f"{k}_trex"] = ev(r[1])
    out[f"{k}_slc"] = ev(r[0], gamma=s["gamma"])
    out[f"{k}_slc_edge"] = ev(r[0], gamma=s["gamma"], strat="edge")
for kk, v in out.items(): print(f"{kk:16s}", v)
json.dump(out, open("results.json", "w"), indent=2)
