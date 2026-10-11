import json, numpy as np
a = json.load(open("results.json"))["fwd_slc_edge"]; b = json.load(open("results2.json"))["fwd_slc_edge"]
w = np.array([1/a[1]**2, 1/b[1]**2]); v = (w @ [a[0], b[0]]) / w.sum()
print("run1", a, "run2", b, "combined", v, "+-", 1/np.sqrt(w.sum()))
