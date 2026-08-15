"""
mission_model.py

Reference mission definition and Tsiolkovsky rocket-equation based
sizing calculations for comparing propellant combinations on an
apples-to-apples basis.
"""

from dataclasses import dataclass
import math

G0 = 9.80665  # standard gravity, m/s^2


@dataclass
class ReferenceMission:
    payload_mass_kg: float = 150.0
    target_orbit: str = "500 km Sun-Synchronous Orbit (SSO)"
    delta_v_budget_m_s: float = 1500.0
    inert_mass_fraction: float = 0.11   # structure/tank/engine mass as fraction of (inert+prop)


def required_mass_ratio(delta_v_m_s: float, isp_s: float) -> float:
    """
    Tsiolkovsky rocket equation, solved for mass ratio (m0/mf).
    delta_v = Isp * g0 * ln(m0/mf)
    """
    ve = isp_s * G0
    return math.exp(delta_v_m_s / ve)


def size_stage(mission: ReferenceMission, isp_s: float):
    """
    Given a mission and an Isp, compute stage sizing:
      - mass ratio
      - propellant mass
      - inert (structure) mass
      - total wet stage mass (excluding payload)
      - payload mass fraction (payload / total wet mass incl. payload)

    Model: m0 = payload + inert + propellant
           mf = payload + inert
           m0/mf = exp(delta_v / (Isp*g0))

    Let inert = f * (inert + propellant)  =>  propellant = inert*(1-f)/f
    Solve self-consistently for inert mass given payload, mass ratio, and f.
    """
    MR = required_mass_ratio(mission.delta_v_budget_m_s, isp_s)
    f = mission.inert_mass_fraction
    payload = mission.payload_mass_kg

    # m0 = payload + inert + prop,  mf = payload + inert
    # m0/mf = MR  =>  payload + inert + prop = MR*(payload+inert)
    # prop = inert*(1-f)/f  (since inert = f*(inert+prop))
    # => payload + inert + inert*(1-f)/f = MR*(payload+inert)
    # => payload + inert/f = MR*payload + MR*inert
    # => inert*(1/f - MR) = MR*payload - payload = payload*(MR-1)
    # => inert = payload*(MR-1) / (1/f - MR)
    denom = (1.0 / f) - MR
    if denom <= 0:
        raise ValueError(
            f"Mission infeasible with Isp={isp_s:.1f}s: required mass ratio "
            f"{MR:.2f} exceeds what inert fraction {f} can support."
        )
    inert = payload * (MR - 1) / denom
    prop = inert * (1 - f) / f
    wet_mass_stage_only = inert + prop           # stage hardware + propellant
    total_mass = wet_mass_stage_only + payload    # full stage incl. payload

    payload_fraction = payload / total_mass

    return {
        "isp_s": isp_s,
        "mass_ratio": MR,
        "propellant_mass_kg": prop,
        "inert_mass_kg": inert,
        "stage_wet_mass_kg": wet_mass_stage_only,
        "total_mass_kg": total_mass,
        "payload_fraction": payload_fraction,
    }
