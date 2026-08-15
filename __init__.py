"""
propellant_tradeoff

Open, reproducible, hardware-validated thermochemical performance modeling
for comparing candidate propulsion technologies (legacy bipropellants,
paraffin/N2O hybrid, HAN-based green monopropellant) for small-satellite
upper-stage / kick-stage applications.
"""

from .propellant_model import (
    LOX_RP1,
    NTO_MMH,
    N2O_PARAFFIN,
    best_isp,
    get_isp_sweep,
    apply_isp_efficiency,
    apply_hybrid_isp_efficiency,
    ISP_EFFICIENCY_FACTOR,
    HYBRID_ISP_EFFICIENCY_FACTOR,
    HAN_MONOPROP_ISP_VAC_S,
    HAN_MONOPROP_DENSITY_KG_M3,
    HYDRAZINE_BASELINE_ISP_VAC_S,
)
from .mission_model import ReferenceMission, size_stage, required_mass_ratio

__all__ = [
    "LOX_RP1",
    "NTO_MMH",
    "N2O_PARAFFIN",
    "best_isp",
    "get_isp_sweep",
    "apply_isp_efficiency",
    "apply_hybrid_isp_efficiency",
    "ISP_EFFICIENCY_FACTOR",
    "HYBRID_ISP_EFFICIENCY_FACTOR",
    "HAN_MONOPROP_ISP_VAC_S",
    "HAN_MONOPROP_DENSITY_KG_M3",
    "HYDRAZINE_BASELINE_ISP_VAC_S",
    "ReferenceMission",
    "size_stage",
    "required_mass_ratio",
]

__version__ = "0.1.0"
