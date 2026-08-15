# Smallsat Upper-Stage Propellant Trade-Off

An open, reproducible, **hardware-validated** thermochemical performance
comparison of candidate propellant technologies for small-satellite
upper-stage / kick-stage propulsion.

Built on [NASA CEA](https://www1.grc.nasa.gov/research-and-engineering/ceaweb/)
via the [`rocketcea`](https://github.com/sonofeft/RocketCEA) Python wrapper,
validated against real published engine performance data, and applied to a
realistic reference mission grounded in operational small-launch vehicles.

## Why this exists

Most propellant trade studies for smallsat upper stages are either
(a) locked behind proprietary tools or paywalled papers with no accompanying
code, or (b) purely qualitative (e.g. weighted decision-matrix methods like
AHP). This project is a from-scratch, open, quantitative alternative: given
a reference mission, it computes theoretical CEA performance, corrects it
against real hardware, and sizes a stage via the Tsiolkovsky rocket equation
— all in a few hundred lines of auditable Python.

**This is explicitly *not* the first comparative study in this space.**
Related prior work includes:
- Sarritzu et al., *"Analytical Hierarchy Process-based trade-off analysis of
  green and hybrid propulsion technologies for upper stage applications,"*
  Int. J. Energetic Materials and Chemical Propulsion, 2023 (qualitative,
  AHP-based).
- Sarritzu & Pasini, *"Performance comparison of green propulsion systems for
  future Orbital Transfer Vehicles,"* Acta Astronautica 217, 2024
  (quantitative, closest prior work to this repo).

This project's contribution is the **open, reproducible, hardware-validated
code artifact** itself, plus an explicit, cited efficiency correction
methodology (see [Validation](#validation) below) that most prior work in
this space does not publish alongside its results.

## What it compares

| Propellant combo | Type | Role in this study |
|---|---|---|
| LOX / RP-1 | Legacy bipropellant | Baseline (e.g. Merlin-class) |
| N2O4 / MMH | Legacy hypergolic bipropellant | Baseline (e.g. Aestus-class) |
| N2O / Paraffin | Hybrid | Emerging, safer-handling candidate |
| HAN-based monopropellant (AF-M315E / ASCENT) | Green monopropellant | NASA GPIM-flown candidate |

## Reference mission

| Parameter | Value | Basis |
|---|---|---|
| Target orbit | 500 km Sun-Synchronous Orbit | Matches ISRO SSLV and most EO smallsats |
| Payload mass | 150 kg | Smallsat class, comparable to SSLV payloads |
| Upper-stage delta-v budget | 1500 m/s | Within published kick-stage range (NASA Smallsat Kickstage concept: up to 1800 m/s) |
| Inert mass fraction | 0.11 | Typical for upper-stage hardware |

## Validation

CEA's default output is **theoretical shifting-equilibrium Isp**: perfect
mixing, no boundary-layer or divergence losses. Real engines never achieve
this. This repo validates the model against three real, published,
flight-proven engines at their exact operating conditions:

| Engine | Published Isp | CEA (theoretical) | Overprediction |
|---|---|---|---|
| Merlin 1D (booster) | 311 s | 337.2 s | +8.4% |
| Merlin 1D Vacuum | 348 s | 369.2 s | +6.1% |
| Aestus (N2O4/MMH) | 324 s | 345.3 s | +6.6% |

This gives a derived **bipropellant Isp efficiency factor of 0.930**,
applied to all bipropellant results in this study.

Hybrid motors (N2O/paraffin) have a *distinct, worse* efficiency profile
than bipropellants, driven by boundary-layer combustion physics unique to
hybrids. Rather than reuse the bipropellant factor, this repo applies a
**separate, literature-derived hybrid factor of 0.840**, based on published
paraffin/N2O hot-fire test data (Isp efficiency of 80.77-87.28% with
mixing-enhancement hardware; see `src/propellant_tradeoff/propellant_model.py`
for full citations).

Run the validation yourself:
```bash
python -m propellant_tradeoff.validation
```

## Results

```bash
python scripts/run_comparison.py
```

| Combo | Delivered Isp | Payload fraction |
|---|---|---|
| LOX/RP-1 | 342.3 s | 0.595 |
| N2O4/MMH | 325.6 s | 0.579 |
| N2O/Paraffin | 267.9 s | 0.511 |
| HAN monoprop (AF-M315E/ASCENT) | 257.0 s | 0.496 |

**Takeaway:** legacy toxic propellants retain a meaningful payload-fraction
advantage over both "green" alternatives once realistic (not theoretical)
efficiency is accounted for. The hybrid and monopropellant options carry a
comparable, non-trivial performance penalty (~0.08-0.10 payload fraction)
in exchange for reduced toxicity, simpler ground handling, and (for the
monopropellant) higher density.

## Repository structure

```
src/propellant_tradeoff/
    propellant_model.py   # CEA wrapper, custom paraffin fuel card, efficiency corrections
    mission_model.py      # Reference mission + Tsiolkovsky rocket equation stage sizing
    validation.py          # Validation against real published engines
scripts/
    run_comparison.py     # Main entry point: runs the full comparison
tests/
    test_mission_model.py     # Pure-math tests (no CEA dependency)
    test_propellant_model.py  # CEA-dependent tests, incl. validation bounds checks
results/
    comparison_results.json   # Output of the last run_comparison.py run
```

## Installation

`rocketcea` wraps a Fortran CEA backend, so a Fortran compiler is required
to build it:

```bash
# Debian/Ubuntu
sudo apt-get install gfortran

pip install -r requirements.txt
```

## Running tests

```bash
python tests/test_mission_model.py
python tests/test_propellant_model.py
```

## Known limitations

- The HAN monopropellant (AF-M315E/ASCENT) Isp is a **literature value**
  (NASA NTRS 20140012587), not CEA-computed — the exact proprietary
  formulation cannot be reconstructed for a first-principles thermochemical
  card. This is intentional and documented, not an oversight.
- The bipropellant efficiency factor (0.930) is derived from only three
  validation engines. A larger validation set would tighten this estimate.
- [`RocketIsp`](https://github.com/sonofeft/RocketIsp) offers a more
  granular, physics-decomposed (JANNAF-method) alternative to the empirical
  efficiency factors used here, but requires real chamber/injector geometry
  that isn't publicly available for the validation engines used in this
  study. Adopting it is a natural extension if such data becomes available.
- Chamber pressure and expansion ratio for each candidate were chosen to be
  representative of upper-stage-class hardware, not optimized per-propellant;
  a full optimization sweep is left as future work.

## Citation

If you use this code, please cite the accompanying paper (details TBD) and
the underlying tools:
- Gordon, S. and McBride, B.J., *Computer Program for Calculation of Complex
  Chemical Equilibrium Compositions*, NASA RP-1311, 1994/1996.
- `rocketcea`: https://github.com/sonofeft/RocketCEA

## License

MIT — see [LICENSE](LICENSE).
