"""
propellant_model.py

Thermochemical performance modeling for candidate upper-stage propellant
combinations, built on NASA CEA (via the rocketcea Python wrapper).

Baselines (legacy, well-characterized -- used to validate the model against
published engine data):
    - LOX / RP-1        (kerolox, e.g. Merlin-class engines)
    - N2O4 / MMH         (storable hypergolic, common on historical upper stages)

Candidates (emerging / underexplored for this specific application):
    - N2O / Paraffin     (self-pressurizing hybrid, active research area)
    - HAN-based monopropellant (AF-M315E-class "green propellant")

NOTE on the HAN monopropellant:
AF-M315E is a proprietary NASA/JPL/AFRL formulation (HAN + fuel + water) and
its exact composition is not publicly available for a from-scratch CEA card.
Rather than guess at a formulation, this module treats it as a *fixed,
literature-sourced* performance point rather than a CEA-computed sweep. This
is called out explicitly wherever it's used, and is standard practice when
working with proprietary/classified-composition propellants in open research.
"""

from dataclasses import dataclass
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

# ---------------------------------------------------------------------------
# Custom propellant thermo cards
# ---------------------------------------------------------------------------
# Paraffin wax (C32H66) is not in CEA's default thermo library. This card
# uses values standard in hybrid-rocket literature (Karabeyoglu et al.,
# Stanford paraffin-hybrid research programme).
_PARAFFIN_CARD = """
fuel paraffin  C 32   H 66
h,cal=-224200.0     t(k)=298.15   wt%=100.00
rho,g/cc = 0.93
"""
add_new_fuel("paraffin", _PARAFFIN_CARD)


@dataclass
class PropellantCombo:
    """A single propellant combination and the CEA object needed to query it."""
    name: str
    ox_name: str
    fuel_name: str
    density_kg_m3: float          # bulk/average propellant density, for volume estimates
    notes: str = ""

    def cea(self) -> CEA_Obj:
        return CEA_Obj(
            oxName=self.ox_name,
            fuelName=self.fuel_name,
            isp_units="sec",
            cstar_units="m/s",
            pressure_units="Bar",
            temperature_units="K",
            sonic_velocity_units="m/s",
            enthalpy_units="J/g",
            density_units="kg/m^3",
            specific_heat_units="J/kg-K",
        )


# ---------------------------------------------------------------------------
# Candidate propellant set
# ---------------------------------------------------------------------------
LOX_RP1 = PropellantCombo(
    name="LOX/RP-1",
    ox_name="LOX",
    fuel_name="RP-1",
    density_kg_m3=1030,  # bulk density at typical MR ~2.3-2.6
    notes="Legacy baseline. Kerolox, e.g. Merlin-class engines.",
)

NTO_MMH = PropellantCombo(
    name="N2O4/MMH",
    ox_name="N2O4",
    fuel_name="MMH",
    density_kg_m3=1200,
    notes="Legacy baseline. Storable hypergolic, common historical upper stage.",
)

N2O_PARAFFIN = PropellantCombo(
    name="N2O/Paraffin",
    ox_name="N2O",
    fuel_name="paraffin",
    density_kg_m3=1100,  # approx bulk average, oxidizer-dominated by mass
    notes="Emerging candidate. Self-pressurizing hybrid, active research area.",
)


def get_isp_sweep(combo: PropellantCombo, Pc_bar: float, eps: float, mr_range):
    """
    Sweep mixture ratio for a given combo and return (mr, isp, cstar, tc) lists.
    """
    C = combo.cea()
    mrs, isps, cstars, tcs = [], [], [], []
    for mr in mr_range:
        try:
            isp = C.get_Isp(Pc=Pc_bar, MR=mr, eps=eps)
            cstar = C.get_Cstar(Pc=Pc_bar, MR=mr)
            tc = C.get_Tcomb(Pc=Pc_bar, MR=mr)
            mrs.append(mr)
            isps.append(isp)
            cstars.append(cstar)
            tcs.append(tc)
        except Exception:
            # Some MR values may be outside CEA's valid solution range; skip them.
            continue
    return mrs, isps, cstars, tcs


def best_isp(combo: PropellantCombo, Pc_bar: float, eps: float, mr_range):
    """Return (best_mr, best_isp, cstar_at_best, tc_at_best) for a combo."""
    mrs, isps, cstars, tcs = get_isp_sweep(combo, Pc_bar, eps, mr_range)
    if not isps:
        raise RuntimeError(f"No valid CEA solutions found for {combo.name}")
    i_best = max(range(len(isps)), key=lambda i: isps[i])
    return mrs[i_best], isps[i_best], cstars[i_best], tcs[i_best]


# ---------------------------------------------------------------------------
# HAN-based monopropellant: literature-sourced fixed performance point
# ---------------------------------------------------------------------------
# AF-M315E (HAN/HAN-blend "green propellant", now formally designated ASCENT --
# Advanced Spacecraft Energetic Non-Toxic), per NASA/AFRL published technical
# data (NASA NTRS 20140012587, GPIM AF-M315E Propulsion System):
#   - Vacuum Isp = 257 s (vs. 235 s for hydrazine baseline, a documented 12%
#     Isp improvement over the propellant it's meant to replace)
#   - 45% denser than hydrazine (1.47 g/cc vs 1.00 g/cc)
# This is a literature/flight-test-derived value, NOT a CEA-computed number,
# because the exact proprietary formulation cannot be reconstructed for a
# first-principles thermochemical card. This distinction is preserved
# through to the results table and discussion.
HAN_MONOPROP_ISP_VAC_S = 257.0   # NASA NTRS 20140012587 (GPIM AF-M315E/ASCENT)
HAN_MONOPROP_DENSITY_KG_M3 = 1470.0  # 1.47 g/cc, NASA NTRS 20140012587
HYDRAZINE_BASELINE_ISP_VAC_S = 235.0  # for reference/discussion, same source


# ---------------------------------------------------------------------------
# Empirical Isp efficiency correction
# ---------------------------------------------------------------------------
# CEA's default output is theoretical shifting-equilibrium Isp: perfect
# mixing/combustion, no boundary-layer or divergence losses. Real engines
# never achieve this. Validation against three published, flight-proven
# engines (Merlin 1D booster, Merlin 1D Vacuum, Aestus) at their published
# operating conditions gives:
#
#   Merlin 1D (booster):   CEA 337.2 s vs published 311 s   (+8.4%)
#   Merlin 1D Vacuum:      CEA 369.2 s vs published 348 s   (+6.1%)
#   Aestus (N2O4/MMH):     CEA 345.3 s vs published 324 s   (+6.6%)
#
# Mean overprediction ~7.0%, consistent with typical literature values for
# Isp efficiency (~93-96% of theoretical shifting equilibrium). We apply a
# single empirical correction factor derived from this validation set to
# convert theoretical CEA Isp into a realistic "delivered" Isp estimate.
ISP_EFFICIENCY_FACTOR = 1 - ((8.4 + 6.1 + 6.6) / 3) / 100.0  # ~0.930


def apply_isp_efficiency(theoretical_isp_s: float) -> float:
    """Apply the empirically-derived Isp efficiency correction (liquid bipropellants)."""
    return theoretical_isp_s * ISP_EFFICIENCY_FACTOR


# ---------------------------------------------------------------------------
# Hybrid-specific Isp efficiency correction
# ---------------------------------------------------------------------------
# Hybrid rocket motors (e.g. N2O/paraffin) have a distinct, generally worse
# combustion-efficiency profile than liquid bipropellants, driven by the
# boundary-layer combustion process unique to hybrids (fuel regresses off a
# solid surface into a diffusion flame, rather than being actively atomized
# and mixed by injectors as in liquid engines). The bipropellant-derived
# ISP_EFFICIENCY_FACTOR above is NOT representative of hybrid motors and
# should not be applied to them.
#
# Literature values for paraffin/N2O-class hybrid motors:
#   - C* efficiency: <80% (axial injection) up to >90% (vortex injection)
#     [Testing of a Long-Burning-Time Paraffin-Based Hybrid Rocket Motor]
#   - With an aft mixing-chamber diaphragm: combustion efficiency 93.9% ->
#     97.34%, but Isp efficiency only 80.77% -> 87.28%
#     [Tian et al. 2013, s11431-013-5325-z]
#   - Passive mixing devices have been shown to raise combustion efficiency
#     by over 40% relative to an unmixed baseline in paraffin/N2O motors
#     [Evaluation of a Paraffin/N2O Hybrid Motor with a Passive Mixing Device]
#
# We take the Isp-efficiency range from the diaphragm study (80.77-87.28%)
# as representative of a reasonably well-designed (mixing-enhanced) hybrid,
# and use the midpoint as our working correction factor. This is explicitly
# lower than, and derived independently from, the bipropellant factor above.
HYBRID_ISP_EFFICIENCY_FACTOR = (0.8077 + 0.8728) / 2  # ~0.840


def apply_hybrid_isp_efficiency(theoretical_isp_s: float) -> float:
    """Apply the literature-derived Isp efficiency correction for N2O/paraffin-class hybrids."""
    return theoretical_isp_s * HYBRID_ISP_EFFICIENCY_FACTOR
