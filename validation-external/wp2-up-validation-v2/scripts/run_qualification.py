#!/usr/bin/env python
"""Execute one WP2-UP-v2 qualification split."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp
import sympy as sp


ROOT = Path(__file__).resolve().parents[3]
VALIDATION = ROOT / "validation-external"
CAMPAIGN = Path(__file__).resolve().parents[1]
for path in (ROOT, VALIDATION):
    sys.path.insert(0, str(path))

from qualification_tools import atomic_write_json, load_json, runtime_fingerprint, sha256_file, utc_now, verify_lock  # noqa: E402
from src.python.ks import KSPhaseState, project_cotangent  # noqa: E402
from src.python.n3bp_qualification import InertialState, SystemParameters  # noqa: E402
from src.python.threebody_flow import canonical_jacobi_flow  # noqa: E402
from src.python.threebody_reduction import JacobiPhaseState  # noqa: E402
from src.python.upstairs_ks import (  # noqa: E402
    UpstairsKSState, lift_jacobi_state, momentum_map_derivative, project_derivative,
    project_state, regularized_hamiltonian, s1_action, upstairs_vector_field,
)


SPATIAL = VALIDATION / "wp3-spatial-validation-v2"
KS = VALIDATION / "wp2-ks-validation/reports"
FLOW = VALIDATION / "wp2-threebody-flow-validation/reports"


def _args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True); parser.add_argument("--corpus", required=True)
    parser.add_argument("--spatial-corpus", required=True); parser.add_argument("--spatial-results", required=True)
    parser.add_argument("--split", choices=("development", "calibration", "holdout"), required=True)
    parser.add_argument("--output", required=True); parser.add_argument("--lock")
    return parser.parse_args()


def _reference():
    path = CAMPAIGN / "reference/autodiff_reference.py"
    spec = importlib.util.spec_from_file_location("wp2_up_v2_autodiff", path)
    if spec is None or spec.loader is None: raise RuntimeError("cannot load autodiff reference")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def _verify_one(expected, lock_path, record_path, prefix):
    lock = verify_lock(lock_path, ROOT, expected_prefix=prefix); record = load_json(record_path)
    if not (
        record.get("status") == "PASS"
        and record.get("qualification_id") == expected["qualification_id"] == lock["qualification_id"]
        and record.get("lock_sha256") == expected["lock_sha256"] == lock["lock_sha256"]
        and sha256_file(record_path) == expected["record_sha256"]
    ): raise RuntimeError(f"invalid prerequisite: {prefix}")
    return {"status": "PASS", "qualification_id": record["qualification_id"], "lock_sha256": lock["lock_sha256"], "record_sha256": sha256_file(record_path)}


def _prerequisites(spec):
    return {
        "wp1_spatial_n3bp": _verify_one(spec["prerequisites"]["wp1_spatial_n3bp"], SPATIAL/"reports/wp3_spatial_v2_qualification_lock.json", SPATIAL/"reports/wp3_spatial_v2_qualification_record.json", "WP1Q-N3BP-SPATIAL-v2"),
        "wp2_kepler_ks": _verify_one(spec["prerequisites"]["wp2_kepler_ks"], KS/"wp2_ks_qualification_lock.json", KS/"wp2_ks_qualification_record.json", "WP2KSQ-v1"),
        "wp2_threebody_flow": _verify_one(spec["prerequisites"]["wp2_threebody_flow"], FLOW/"wp2_threebody_flow_qualification_lock.json", FLOW/"wp2_threebody_flow_qualification_record.json", "WP2-3BFLOWQ-v1"),
    }


def _verify_spatial_inputs(split: str, corpus_path: str, results_path: str) -> None:
    record = load_json(SPATIAL/"reports/wp3_spatial_v2_qualification_record.json")
    corpus_evidence = record["evidence_files"]["corpus"]
    if sha256_file(corpus_path) != corpus_evidence["sha256"]: raise RuntimeError("spatial corpus hash mismatch")
    evaluation_evidence = record["evidence_files"][f"{split}_evaluation"]
    evaluation_path = ROOT / evaluation_evidence["path"]
    if sha256_file(evaluation_path) != evaluation_evidence["sha256"]: raise RuntimeError("spatial evaluation hash mismatch")
    evaluation = load_json(evaluation_path)
    if evaluation["status"] != "PASS" or evaluation["results_sha256"] != sha256_file(results_path):
        raise RuntimeError("spatial split result is not the qualified input")


def _scaled(first, second):
    left, right = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    return float(np.max(np.abs(left-right))/max(1.0, float(np.max(np.abs(right)))))


def _project_unchecked(state):
    pair = project_cotangent(KSPhaseState(state.q, state.Q), require_zero_level=False)
    return np.concatenate((pair.x, state.lambda_vector, pair.p, state.p_lambda))


def _rotate_vector(vector, angle):
    return s1_action(UpstairsKSState.from_vector(vector), angle).as_vector()


def _gradient_error(state, parameters, energy, step):
    vector = state.as_vector(); gradient = np.empty(14)
    for index in range(14):
        offset = np.zeros(14); offset[index] = step
        plus = regularized_hamiltonian(UpstairsKSState.from_vector(vector+offset), parameters, energy)
        minus = regularized_hamiltonian(UpstairsKSState.from_vector(vector-offset), parameters, energy)
        gradient[index] = (plus-minus)/(2*step)
    return _scaled(upstairs_vector_field(state, parameters, energy).derivative, np.concatenate((gradient[7:], -gradient[:7])))


def _angular_lie(physical, tangent):
    rho, lam, p_rho, p_lam = physical.reshape(4,3); drho, dlam, dp_rho, dp_lam = tangent.reshape(4,3)
    lie = np.cross(drho,p_rho)+np.cross(rho,dp_rho)+np.cross(dlam,p_lam)+np.cross(lam,dp_lam)
    scale = max(1.0, np.linalg.norm(rho)*np.linalg.norm(p_rho), np.linalg.norm(lam)*np.linalg.norm(p_lam))
    return float(np.max(np.abs(lie))/scale)


def _integrate(state, parameters, energy, horizon, execution):
    initial_h = regularized_hamiltonian(state, parameters, energy); initial_xi = state.xi
    def rhs(_s, value): return upstairs_vector_field(UpstairsKSState.from_vector(value), parameters, energy).derivative
    solution = solve_ivp(rhs, (0.0,horizon), state.as_vector(), method="DOP853", rtol=float(execution["integration_rtol"]), atol=float(execution["integration_atol"]), max_step=float(execution["integration_max_step"]))
    if not solution.success: raise RuntimeError(solution.message)
    final = UpstairsKSState.from_vector(solution.y[:,-1])
    h_drift = abs(regularized_hamiltonian(final, parameters, energy)-initial_h)/max(1.0,abs(energy))
    xi_drift = abs(final.xi-initial_xi)
    return final, h_drift, xi_drift


def _short_projection(shell, parameters, execution):
    horizon = float(execution["short_flow_s_horizon"])
    initial = np.concatenate((shell.state.as_vector(), [0.0]))
    def up_rhs(_s, value):
        flow = upstairs_vector_field(UpstairsKSState.from_vector(value[:14]), parameters, shell.energy)
        return np.concatenate((flow.derivative,[flow.physical_time_rate]))
    up = solve_ivp(up_rhs,(0,horizon),initial,method="DOP853",rtol=float(execution["integration_rtol"]),atol=float(execution["integration_atol"]),max_step=float(execution["integration_max_step"]))
    final_up = UpstairsKSState.from_vector(up.y[:14,-1]); physical_time=float(up.y[14,-1]); physical_initial=project_state(shell.state)
    def physical_rhs(_t,value): return canonical_jacobi_flow(value,parameters).derivative
    physical = solve_ivp(physical_rhs,(0,physical_time),physical_initial,method="DOP853",rtol=float(execution["integration_rtol"]),atol=float(execution["integration_atol"]),max_step=max(physical_time/20,1e-10))
    return _scaled(_project_unchecked(final_up),physical.y[:,-1])


def _collision_metrics(shell, parameters, execution):
    m1,m2,_=(float(value) for value in parameters.masses); mu=m1*m2/(m1+m2); k=float(parameters.gravitational_constant)*m1*m2
    direction=np.array([1.0,0.0,0.0,0.0]); q_momentum=np.sqrt(8*mu*k)*direction
    collision=UpstairsKSState(np.zeros(4),shell.state.lambda_vector,q_momentum,shell.state.p_lambda)
    collision_flow=upstairs_vector_field(collision,parameters,shell.energy)
    errors=[]
    for epsilon in execution["collision_limit_epsilons"]:
        q=float(epsilon)*direction
        probe=UpstairsKSState(q,shell.state.lambda_vector,q_momentum,shell.state.p_lambda)
        # Correct the radial momentum magnitude onto K_h=0 while preserving Xi=0.
        residual=regularized_hamiltonian(probe,parameters,shell.energy)
        corrected_squared=float(np.dot(q_momentum,q_momentum))-8*mu*residual
        if corrected_squared <= 0: raise RuntimeError("collision shell correction became nonpositive")
        probe=UpstairsKSState(q,shell.state.lambda_vector,np.sqrt(corrected_squared)*direction,shell.state.p_lambda)
        errors.append(_scaled(upstairs_vector_field(probe,parameters,shell.energy).derivative,collision_flow.derivative))
    horizon=float(execution["collision_flow_s_horizon"])
    plus,h_plus,xi_plus=_integrate(collision,parameters,shell.energy,horizon,execution)
    minus,h_minus,xi_minus=_integrate(collision,parameters,shell.energy,-horizon,execution)
    crossing=bool(np.dot(plus.q,direction)>0 and np.dot(minus.q,direction)<0)
    return {
        "collision_shell_abs": abs(regularized_hamiltonian(collision,parameters,shell.energy)),
        "collision_limit_scaled": errors[-1],
        "collision_limit_monotone": float(all(later <= earlier*(1+1e-10) for earlier,later in zip(errors,errors[1:]))),
        "collision_passage_finite": float(crossing and np.all(np.isfinite(plus.as_vector())) and np.all(np.isfinite(minus.as_vector()))),
        "collision_passage_hamiltonian_drift_scaled": max(h_plus,h_minus),
        "collision_passage_xi_drift_abs": max(xi_plus,xi_minus),
    }


def _symbolic_identity():
    q=sp.symbols("q0:4", real=True); Q=sp.symbols("Q0:4", real=True)
    a,b,c,d=q; x=sp.Matrix([2*(a*c+b*d),2*(a*d-b*c),a*a+b*b-c*c-d*d]); jac=x.jacobian(q)
    radius=sum(value*value for value in q); xi=-b*Q[0]+a*Q[1]-d*Q[2]+c*Q[3]
    expression=sp.expand((jac*sp.Matrix(Q)).dot(jac*sp.Matrix(Q))-4*radius*sum(value*value for value in Q)+4*xi*xi)
    return int(expression == 0)


def _checkpoint(state,parameters,angle,reference,execution,integrate):
    jacobi=JacobiPhaseState.from_inertial(state,parameters).quotient.as_canonical_vector(); shell=lift_jacobi_state(jacobi,parameters,angle=angle)
    flow=upstairs_vector_field(shell.state,parameters,shell.energy); ref_h,ref_v=reference.evaluate(shell.state.as_vector(),np.asarray(parameters.masses),float(parameters.gravitational_constant),shell.energy)
    physical=canonical_jacobi_flow(jacobi,parameters); projected=project_derivative(flow); transformed=s1_action(shell.state,.731); transformed_flow=upstairs_vector_field(transformed,parameters,shell.energy)
    metrics={
        "autodiff_hamiltonian_scaled": _scaled(flow.hamiltonian,ref_h), "autodiff_vector_field_scaled": _scaled(flow.derivative,ref_v),
        "shell_hamiltonian_scaled": abs(flow.hamiltonian)/max(1.0,abs(shell.energy)), "xi_level_abs": abs(shell.state.xi),
        "roundtrip_scaled": _scaled(project_state(shell.state),jacobi), "sundman_projection_scaled": _scaled(projected,shell.state.radius*physical.derivative),
        "canonical_gradient_scaled": _gradient_error(shell.state,parameters,shell.energy,float(execution["finite_difference_step"])),
        "s1_hamiltonian_scaled": _scaled(regularized_hamiltonian(transformed,parameters,shell.energy),flow.hamiltonian),
        "s1_projection_scaled": _scaled(project_state(transformed),jacobi), "s1_vector_covariance_scaled": _scaled(transformed_flow.derivative,_rotate_vector(flow.derivative,.731)),
        "xi_lie_abs": abs(momentum_map_derivative(flow)),
        "projected_angular_momentum_lie_scaled": _angular_lie(jacobi,projected/max(shell.state.radius,np.finfo(float).tiny)),
        "short_flow_projection_scaled": _short_projection(shell,parameters,execution) if integrate else 0.0,
    }
    metrics.update(_collision_metrics(shell,parameters,execution) if integrate else {name:0.0 for name in ("collision_shell_abs","collision_limit_scaled","collision_limit_monotone","collision_passage_finite","collision_passage_hamiltonian_drift_scaled","collision_passage_xi_drift_abs")})
    return metrics


def main():
    args=_args(); spec,corpus=load_json(args.spec),load_json(args.corpus); spatial_corpus=load_json(args.spatial_corpus); spatial_results=load_json(args.spatial_results)
    if corpus["spec_sha256"]!=sha256_file(args.spec) or corpus["spatial_corpus_sha256"]!=sha256_file(args.spatial_corpus): raise RuntimeError("WP2-UP-v2 corpus mismatch")
    _verify_spatial_inputs(args.split,args.spatial_corpus,args.spatial_results)
    lock=None
    if args.split=="holdout":
        if not args.lock: raise RuntimeError("holdout execution requires the WP2-UP-v2 lock")
        lock=verify_lock(args.lock,ROOT,expected_prefix=spec["campaign"])
    prerequisites=_prerequisites(spec); definitions={case["case_id"]:case for case in spatial_corpus["cases"]}; source_results={case["case_id"]:case for case in spatial_results["cases"]}; reference=_reference(); cases=[]
    for definition in (case for case in corpus["cases"] if case["split"]==args.split):
        source_id=definition["source_case_id"]; source_def=definitions[source_id]; source=source_results[source_id]; parameters=SystemParameters([float(v) for v in source_def["masses_decimal"]],gravitational_constant=1.0); rows=[]
        for offset,checkpoint in enumerate(definition["checkpoint_indices"]):
            state=InertialState(np.asarray(source["oracle"]["states_decimal"][checkpoint],dtype=float)); rows.append(_checkpoint(state,parameters,float(definition["gauge_angle"]),reference,spec["execution"],offset==0))
        metrics={name:max(float(row[name]) for row in rows) for name in rows[0]}; cases.append({"case_id":definition["case_id"],"source_case_id":source_id,"source_family":definition["source_family"],"success":bool(all(np.isfinite(value) for value in metrics.values())),"metrics":metrics})
    payload: dict[str,Any]={"schema_version":"1.0","campaign":spec["campaign"],"split":args.split,"generated_utc":utc_now(),"spec_sha256":sha256_file(args.spec),"corpus_sha256":sha256_file(args.corpus),"spatial_corpus_sha256":sha256_file(args.spatial_corpus),"spatial_results_sha256":sha256_file(args.spatial_results),"upstream_input_hash_verified":1.0,"prerequisites":prerequisites,"runtime":runtime_fingerprint(),"cases":cases,"structural":{"symbolic_ks_kinetic_identity_pass":_symbolic_identity(),"simultaneous_regularization_qualified":0,"unseen_scientific_holdout":0}}
    if lock is not None: payload["qualification_id"]=lock["qualification_id"]; payload["lock_sha256"]=lock["lock_sha256"]
    atomic_write_json(args.output,payload); print(f"wrote {args.split} evidence for {len(cases)} WP2-UP-v2 cases")


if __name__ == "__main__": main()
