"""Shared setup: credentials, backend, fixed problem definition (copied from the MAIN PROMPT)."""
import os, json, logging
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

logging.getLogger("qiskit_ibm_runtime").setLevel(logging.ERROR)
HERE = os.path.dirname(os.path.abspath(__file__))

# API key lives in .env (git-ignored), never in code
for line in open(os.path.join(HERE, ".env")):
    if "=" in line:
        k, v = line.strip().split("=", 1)
        os.environ[k] = v
os.environ["QC_API_KEY"] = os.environ["IBM_API_KEY"]   # used by qc_grader

JOBS_FILE = os.path.join(HERE, "job_ids.json")

def load_jobs():
    return json.load(open(JOBS_FILE)) if os.path.exists(JOBS_FILE) else {}

def save_job(name, job_id):
    jobs = load_jobs(); jobs[name] = job_id
    json.dump(jobs, open(JOBS_FILE, "w"), indent=2)

def get_service():
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService(channel="ibm_quantum_platform", token=os.environ["IBM_API_KEY"])

# ---- Fixed problem definition (do not change) ----
NUM_QUBITS = 15
NUM_TROTTER_STEPS = 8
RX_ANGLE = np.pi / 4

def construct_ising_circuit(num_qubits, num_trotter_steps, rx_angle, barrier=False):
    qc = QuantumCircuit(num_qubits)
    for _ in range(num_trotter_steps):
        qc.rx(rx_angle, range(num_qubits))
        if barrier:
            qc.barrier()
        for first_qubit in (1, 2):
            for idx in range(first_qubit, num_qubits, 2):
                qc.sdg([idx - 1, idx])
                qc.cz(idx - 1, idx)
        if barrier:
            qc.barrier()
    return qc

circuit = construct_ising_circuit(NUM_QUBITS, NUM_TROTTER_STEPS, RX_ANGLE)
circuit_mirror = QuantumCircuit(NUM_QUBITS)
circuit_mirror.compose(circuit, inplace=True)
circuit_mirror.barrier()
circuit_mirror.compose(circuit.inverse(), inplace=True)

MID = NUM_QUBITS // 2  # = 7
observable = SparsePauliOp.from_sparse_list([("ZZ", [MID - 1, MID], 1.0)], num_qubits=NUM_QUBITS)
