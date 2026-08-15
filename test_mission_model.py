"""
Tests for mission_model.py -- the Tsiolkovsky rocket equation and stage
sizing calculations. These are pure math and don't require CEA, so they
run fast and don't depend on rocketcea being installed correctly.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from propellant_tradeoff.mission_model import (
    ReferenceMission, required_mass_ratio, size_stage, G0,
)


def test_required_mass_ratio_zero_delta_v():
    # Zero delta-v should require a mass ratio of exactly 1 (no propellant needed)
    mr = required_mass_ratio(delta_v_m_s=0.0, isp_s=300.0)
    assert math.isclose(mr, 1.0, rel_tol=1e-9)


def test_required_mass_ratio_matches_tsiolkovsky():
    # Sanity check against the rocket equation solved by hand:
    # delta_v = Isp * g0 * ln(MR)  =>  MR = exp(delta_v / (Isp*g0))
    isp = 320.0
    dv = 2000.0
    expected = math.exp(dv / (isp * G0))
    assert math.isclose(required_mass_ratio(dv, isp), expected, rel_tol=1e-9)


def test_size_stage_mass_balance_closes():
    # The three mass components (payload, inert, propellant) must sum to
    # exactly the reported total mass -- this is a hard physical constraint,
    # not just a sanity check.
    mission = ReferenceMission(payload_mass_kg=150.0, delta_v_budget_m_s=1500.0,
                                inert_mass_fraction=0.11)
    result = size_stage(mission, isp_s=320.0)
    computed_total = (mission.payload_mass_kg
                       + result["inert_mass_kg"]
                       + result["propellant_mass_kg"])
    assert math.isclose(computed_total, result["total_mass_kg"], rel_tol=1e-9)


def test_size_stage_inert_fraction_is_respected():
    # By construction, inert / (inert + propellant) should equal the
    # mission's specified inert_mass_fraction.
    mission = ReferenceMission(inert_mass_fraction=0.11)
    result = size_stage(mission, isp_s=320.0)
    stage_only = result["inert_mass_kg"] + result["propellant_mass_kg"]
    assert math.isclose(result["inert_mass_kg"] / stage_only, 0.11, rel_tol=1e-6)


def test_higher_isp_gives_higher_payload_fraction():
    # Physically, a more efficient (higher Isp) propellant should always
    # require less propellant mass for the same delta-v, and therefore
    # yield a higher payload fraction, all else equal.
    mission = ReferenceMission()
    low_isp_result = size_stage(mission, isp_s=250.0)
    high_isp_result = size_stage(mission, isp_s=350.0)
    assert high_isp_result["payload_fraction"] > low_isp_result["payload_fraction"]


def test_infeasible_mission_raises():
    # A very low Isp combined with a large delta-v budget and a tight inert
    # fraction should be physically infeasible and must raise, not silently
    # return nonsense (e.g. negative masses).
    mission = ReferenceMission(delta_v_budget_m_s=8000.0, inert_mass_fraction=0.05)
    try:
        size_stage(mission, isp_s=200.0)
        assert False, "Expected ValueError for infeasible mission, but none was raised"
    except ValueError:
        pass


if __name__ == "__main__":
    test_functions = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for fn in test_functions:
        fn()
        print(f"PASSED: {fn.__name__}")
    print(f"\nAll {len(test_functions)} tests passed.")
