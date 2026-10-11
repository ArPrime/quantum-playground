"""CPU: SLC backward/forward bounds for <Z6Z7> on both circuits. Saved to bounds.pkl."""
exec(open("prep.py").read())
import pickle, time
from qiskit_addon_slc.bounds import compute_backward_bounds, compute_forward_bounds, tighten_with_speed_limit
from qiskit_addon_slc.utils import generate_noise_model_paulis

out = {}
for k in ["fwd", "mirror"]:
    t = time.time()
    nmp = generate_noise_model_paulis(uniq[k], backend.coupling_map, boxed[k])
    obs_isa = observable.apply_layout(layout, num_qubits=isa[k].num_qubits)
    bwd = compute_backward_bounds(boxed[k], nmp, evolution_max_terms=1000, timeout=120)
    fwd = compute_forward_bounds(boxed[k], nmp, obs_isa, evolution_max_terms=1000,
                                 eigval_max_qubits=18, atol=1e-8, timeout=120)
    fwd = tighten_with_speed_limit(fwd, boxed[k], nmp, obs_isa)
    out[k] = dict(nmp=nmp, bwd=bwd, fwd=fwd)
    print(f"{k}: bounds done in {time.time()-t:.0f}s")
pickle.dump(out, open("bounds.pkl", "wb"))
