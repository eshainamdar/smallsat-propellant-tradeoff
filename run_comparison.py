#!/usr/bin/env python3
"""
run_comparison.py

Runs the full propellant comparison for the reference small-satellite
upper-stage mission: for each candidate propellant combination, finds the
best-Isp operating point (or uses a literature value for the HAN
monopropellant), applies the appropriate Isp efficiency correction, sizes
the stage via the Tsiolkovsky rocket equation, and reports mass ratio,
propellant mass, and payload fraction.

Usage:
    python scripts/run_comparison.py
"""

import json
import sys
from pathlib import Path

# Allow running directly from the scripts/ dir without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from propellant_tradeoff import (
    LOX_RP1, NTO_MMH, N2O_PARAFFIN,
    best_isp, apply_isp_efficiency, apply_hybrid_isp_efficiency,
    ISP_EFFICIENCY_FACTOR, HYBRID_ISP_EFFICIENCY_FACTOR,
    HAN_MONOPROP_ISP_VAC_S,
    ReferenceMission, size_stage,
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

mission = ReferenceMission()

# Chamber pressure / expansion ratio per combo (upper-stage-appropriate).
# Hybrids typically run lower Pc than liquid bipropellants.
CONDITIONS = {
    LOX_RP1.name:      dict(Pc_bar=25, eps=80, mr_range=[x / 100 for x in range(180, 320, 4)]),
    NTO_MMH.name:      dict(Pc_bar=25, eps=80, mr_range=[x / 100 for x in range(140, 260, 4)]),
    N2O_PARAFFIN.name: dict(Pc_bar=25, eps=60, mr_range=[x / 10 for x in range(50, 100, 2)]),
}


def main():
    results = []

    print(f"Reference mission: {mission.target_orbit}, payload={mission.payload_mass_kg} kg, "
          f"delta-v={mission.delta_v_budget_m_s} m/s, inert fraction={mission.inert_mass_fraction}\n")
    print(f"Isp efficiency factor (bipropellant, hardware-validated): {ISP_EFFICIENCY_FACTOR:.3f}")
    print(f"Isp efficiency factor (hybrid, literature-derived):       {HYBRID_ISP_EFFICIENCY_FACTOR:.3f}\n")

    for combo in [LOX_RP1, NTO_MMH, N2O_PARAFFIN]:
        cond = CONDITIONS[combo.name]
        mr, isp_theoretical, cstar, tc = best_isp(combo, cond["Pc_bar"], cond["eps"], cond["mr_range"])
        if combo is N2O_PARAFFIN:
            isp_delivered = apply_hybrid_isp_efficiency(isp_theoretical)
            eff_source = "hybrid-specific (literature test data)"
        else:
            isp_delivered = apply_isp_efficiency(isp_theoretical)
            eff_source = "bipropellant (hardware-validated)"
        sizing = size_stage(mission, isp_delivered)
        results.append({
            "combo": combo.name,
            "efficiency_source": eff_source,
            "MR": mr,
            "isp_theoretical_s": isp_theoretical,
            "isp_delivered_s": isp_delivered,
            "cstar_m_s": cstar,
            "Tc_K": tc,
            **sizing,
        })

    # HAN-based monopropellant: literature-sourced Isp is already a
    # *delivered* (real, flight-test-derived) value -- no correction applied.
    sizing = size_stage(mission, HAN_MONOPROP_ISP_VAC_S)
    results.append({
        "combo": "HAN monoprop (AF-M315E / ASCENT)",
        "efficiency_source": "literature (NASA NTRS 20140012587, already delivered)",
        "MR": None,
        "isp_theoretical_s": None,
        "isp_delivered_s": HAN_MONOPROP_ISP_VAC_S,
        "cstar_m_s": None,
        "Tc_K": None,
        **sizing,
    })

    header = (f"{'Combo':32s} {'Isp_deliv(s)':>12s} {'MR':>6s} {'MassRatio':>10s} "
              f"{'Prop(kg)':>10s} {'Stage(kg)':>10s} {'PL frac':>8s}")
    print(header)
    print("-" * len(header))
    for r in results:
        mr_str = f"{r['MR']:.2f}" if r["MR"] is not None else "n/a"
        print(f"{r['combo']:32s} {r['isp_delivered_s']:12.1f} {mr_str:>6s} "
              f"{r['mass_ratio']:10.3f} {r['propellant_mass_kg']:10.1f} "
              f"{r['stage_wet_mass_kg']:10.1f} {r['payload_fraction']:8.3f}")

    out_path = RESULTS_DIR / "comparison_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
