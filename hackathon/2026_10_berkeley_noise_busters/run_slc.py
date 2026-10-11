"""Build SLC-mitigated Executor programs for fwd + mirror, submit (or reuse) jobs."""
exec(open("prep.py").read())
import pickle, samplomatic
from qiskit.transpiler import PassManager
from qiskit_addon_slc.bounds import merge_bounds, compute_local_scales
from qiskit_addon_slc.utils import map_modifier_ref_to_ref
from qiskit_addon_utils.exp_vals.measurement_bases import get_measurement_bases
from qiskit_addon_utils.exp_vals.observable_mappings import map_observable_virtual_to_canonical
from qiskit_addon_utils.noise_management import gamma_from_noisy_boxes
from qiskit_addon_utils.noise_management.post_selection.transpiler.passes import AddPostSelectionMeasures, AddSpectatorMeasures
from qiskit_ibm_runtime import Executor, QuantumProgram

jobs = load_jobs()
nl_result = service.job(jobs["noise_learning"]).result()
B = pickle.load(open("bounds.pkl", "rb"))
NUM_RAND, SHOTS = 256, 128
state = {}
for k in ["fwd", "mirror"]:
    refs = nl_result.to_dict(uniq[k], require_refs=False)
    id_map = map_modifier_ref_to_ref(boxed[k])
    merged = merge_bounds(boxed[k], B[k]["fwd"], B[k]["bwd"], refs)
    ls, cost, bias = compute_local_scales(boxed[k], merged, refs, sampling_cost_budget=np.inf, bias_tolerance=1e-3)
    gamma = gamma_from_noisy_boxes(refs, id_map, ls)
    gamma_full = gamma_from_noisy_boxes(refs, id_map)
    print(f"{k}: SLC gamma^2={gamma**2:.2f}  full PEC gamma^2={gamma_full**2:.2f}  bias bound={bias:.2e}")
    meas_box = boxed[k].data[-1]
    canon = [i for i, q in enumerate(boxed[k].qubits) if q in meas_box.qubits]
    obs_canon = map_observable_virtual_to_canonical(observable, layout, canon)
    bases, rev = get_measurement_bases(obs_canon)
    _, rev_meas = get_measurement_bases(observable)
    tmpl, samplex = samplomatic.build(boxed[k])
    final_tmpl = PassManager([AddSpectatorMeasures(backend.coupling_map), AddPostSelectionMeasures(x_pulse_type="rx")]).run(tmpl)
    basis_key = next(s.name.split(".", 1)[1] for s in samplex.inputs().get_specs("basis_changes"))
    nrefs = [s.name.split(".", 1)[1] for s in samplex.inputs().get_specs("noise_scales")]
    prog = QuantumProgram(shots=SHOTS, noise_maps=refs)
    for scale in (-1.0, 0.0):   # item 0: SLC-mitigated, item 1: unmitigated (twirled)
        inp = {f"noise_scales.{r}": scale for r in nrefs} | {"basis_changes": {basis_key: bases[0]}}
        if scale < 0: inp |= {"local_scales": ls}
        prog.append_samplex_item(circuit=final_tmpl, samplex=samplex,
            samplex_arguments=samplex.inputs().make_broadcastable().bind(**inp), shape=(NUM_RAND,))
    key = f"executor_{k}"
    if key not in jobs:
        j = Executor(backend).run(prog); save_job(key, j.job_id()); print("submitted", key, j.job_id())
    state[k] = dict(gamma=gamma, gamma_full=gamma_full, rev=rev, rev_meas=rev_meas, final_tmpl=final_tmpl)
pickle.dump(state, open("slc_state.pkl", "wb"))
