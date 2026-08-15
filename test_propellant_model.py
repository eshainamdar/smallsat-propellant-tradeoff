"""
Tests for propellant_model.py and validation.py. These DO require rocketcea
(and its NASA CEA Fortran backend) to be installed and working, since they
run real thermochemical calculations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from propellant_tradeoff import LOX_RP1, NTO_MMH, N2O_PARAFFIN, best_isp
from propellant_tradeoff.validation import run_validation, derive_efficiency_factor


def test_lox_rp1_isp_in_realistic_range():
    # LOX/RP-1 vacuum Isp for any reasonable Pc/eps should land in the
    # 280-380s range; anything wildly outside that indicates a broken
    # CEA install or a bad card, not a real engine result.
    mr, isp, cstar, tc = best_isp(LOX_RP1, Pc_bar=70, eps=16, mr_range=[2.0, 2.27, 2.56, 2.8])
    assert 280 < isp < 380


def test_paraffin_fuel_card_loads_and_computes():
    # This specifically checks that the custom paraffin fuel thermo card
    # (not in CEA's default library) was registered correctly and produces
    # a physically reasonable Isp for N2O/paraffin.
    mr, isp, cstar, tc = best_isp(N2O_PARAFFIN, Pc_bar=25, eps=50, mr_range=[5, 6, 7, 8])
    assert 250 < isp < 340


def test_validation_cases_all_overpredict_theoretical_vs_real():
    # CEA's theoretical shifting-equilibrium Isp should ALWAYS be >= the
    # real published Isp for these validation engines (theory is an upper
    # bound on real delivered performance -- if this fails, something is
    # wrong with the CEA setup, e.g. wrong Pc/eps/MR for the engine).
    results = run_validation()
    for r in results:
        assert r["cea_theoretical_isp_s"] >= r["published_isp_s"], (
            f"{r['engine']}: theoretical Isp ({r['cea_theoretical_isp_s']:.1f}s) "
            f"should exceed published real Isp ({r['published_isp_s']:.1f}s)"
        )


def test_validation_overprediction_within_expected_bounds():
    # Real engines typically achieve 90-97% of theoretical shifting
    # equilibrium Isp (a well-documented range in propulsion literature).
    # Overprediction outside roughly 3-12% would suggest a modeling error.
    results = run_validation()
    for r in results:
        assert 2.0 < r["pct_overprediction"] < 12.0, (
            f"{r['engine']}: overprediction of {r['pct_overprediction']:.1f}% "
            f"is outside the expected 2-12% range for real engines"
        )


def test_derived_efficiency_factor_is_reasonable():
    factor = derive_efficiency_factor()
    assert 0.85 < factor < 0.98


if __name__ == "__main__":
    test_functions = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for fn in test_functions:
        fn()
        print(f"PASSED: {fn.__name__}")
    print(f"\nAll {len(test_functions)} tests passed.")
