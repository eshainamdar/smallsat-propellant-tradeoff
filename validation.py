"""
validation.py

Validates the theoretical CEA model against real, published, flight-proven
rocket engines. This module is the empirical basis for the Isp efficiency
correction factors used elsewhere in this package (see propellant_model.py).

Reference data sources (see README for full citations):
    - Merlin 1D (booster):   astronautix.com/m/merlin1d.html
    - Merlin 1D Vacuum:      astronautix.com/m/merlin1dvac.html
    - Aestus (Ariane 5):     Wikipedia "Aestus" (sourced to Astrium/ESA data)
"""

from dataclasses import dataclass
from .propellant_model import LOX_RP1, NTO_MMH


@dataclass
class ValidationCase:
    engine_name: str
    combo_name: str
    Pc_bar: float
    eps: float
    MR: float
    published_isp_vac_s: float
    source: str


VALIDATION_CASES = [
    ValidationCase(
        engine_name="Merlin 1D (booster, sea-level nozzle)",
        combo_name="LOX/RP-1",
        Pc_bar=96, eps=16, MR=2.36,
        published_isp_vac_s=311.0,
        source="astronautix.com/m/merlin1d.html",
    ),
    ValidationCase(
        engine_name="Merlin 1D Vacuum (extended nozzle)",
        combo_name="LOX/RP-1",
        Pc_bar=96, eps=120, MR=2.36,
        published_isp_vac_s=348.0,
        source="astronautix.com/m/merlin1dvac.html",
    ),
    ValidationCase(
        engine_name="Aestus (Ariane 5 upper stage)",
        combo_name="N2O4/MMH",
        Pc_bar=11, eps=84, MR=1.9,
        published_isp_vac_s=324.0,
        source="Wikipedia: Aestus (Astrium/ESA data)",
    ),
]

_COMBO_LOOKUP = {LOX_RP1.name: LOX_RP1, NTO_MMH.name: NTO_MMH}


def run_validation():
    """
    Run all validation cases and return a list of dicts with theoretical
    CEA Isp, published Isp, and percent difference for each case.
    """
    results = []
    for case in VALIDATION_CASES:
        combo = _COMBO_LOOKUP[case.combo_name]
        C = combo.cea()
        isp_theoretical = C.get_Isp(Pc=case.Pc_bar, MR=case.MR, eps=case.eps)
        pct_diff = 100 * (isp_theoretical - case.published_isp_vac_s) / case.published_isp_vac_s
        results.append({
            "engine": case.engine_name,
            "combo": case.combo_name,
            "published_isp_s": case.published_isp_vac_s,
            "cea_theoretical_isp_s": isp_theoretical,
            "pct_overprediction": pct_diff,
            "source": case.source,
        })
    return results


def derive_efficiency_factor(results=None) -> float:
    """
    Derive the empirical Isp efficiency correction factor as the mean
    overprediction across all validation cases. Returns a multiplicative
    factor (e.g. 0.930 means CEA overpredicts by ~7% on average).
    """
    if results is None:
        results = run_validation()
    mean_pct = sum(r["pct_overprediction"] for r in results) / len(results)
    return 1 - mean_pct / 100.0


if __name__ == "__main__":
    results = run_validation()
    print(f"{'Engine':40s} {'Published':>10s} {'CEA Theor.':>11s} {'Diff':>7s}")
    print("-" * 72)
    for r in results:
        print(f"{r['engine']:40s} {r['published_isp_s']:10.1f} "
              f"{r['cea_theoretical_isp_s']:11.1f} {r['pct_overprediction']:+6.1f}%")
    factor = derive_efficiency_factor(results)
    print(f"\nDerived Isp efficiency factor: {factor:.3f}")
