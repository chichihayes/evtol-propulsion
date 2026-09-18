# Case Study: Pipistrel Velis Electro — First EASA Type-Certified Electric Aircraft

**Status:** Original summary written for this knowledge base, based on publicly
reported facts. Not a reproduction of any single source document — verify
details against primary sources before relying on specific figures.

**Source facts drawn from:** EASA newsroom announcement of the type
certificate, and the aircraft's publicly available specifications.
See: https://www.easa.europa.eu/newsroom-and-events/press-releases/easa-certifies-electric-aircraft-first-type-certification-fully

## Summary

On 18 May 2020, EASA issued Type Certificate EASA.A.573 to the Pipistrel
Velis Electro, making it the first fully electric aircraft to receive type
certification from a major civil aviation authority. The aircraft is a
two-seat trainer, certified under EASA CS-23 with a bespoke certification
basis reflecting its electric powertrain (there was no dedicated electric
propulsion special condition in force at the time of this program — SC E-19
was published afterward, in 2021).

Key characteristics relevant to feasibility/readiness lessons:

- **Powertrain:** a single type-certified electric engine, driving a
  fixed-pitch propeller.
- **Energy storage:** a liquid-cooled battery system arranged as two
  battery packs connected in parallel, giving physical/electrical redundancy
  at the pack level.
- **Mission profile:** short-endurance (well under an hour plus reserve),
  which simplified the battery-energy and thermal-management certification
  problem relative to longer-range eVTOL missions.
- **Certification path:** achieved by treating the electric powertrain as a
  novel technology under the existing CS-23 framework via special
  conditions/equivalent safety findings, rather than waiting for a
  purpose-built electric-propulsion certification standard.

## Why this matters for readiness assessment

- It demonstrates that a **simple, low-redundancy, short-endurance** electric
  architecture was certifiable years before the eVTOL-specific SC-VTOL / SC
  E-19 framework existed — suggesting programs that minimize architectural
  novelty (single motor, simple battery topology, short mission) can reach
  certification faster than highly redundant multi-motor distributed
  propulsion designs.
- It is a useful **lower bound / reference point** on TRL and certification
  schedule for any new design: a design that is architecturally *more*
  complex than the Velis Electro (more motors, higher redundancy, longer
  endurance, higher voltage) should be expected to take longer and face more
  open certification questions than this program did, not less.
- It does **not** provide direct precedent for multi-motor distributed
  electric propulsion, high-voltage fast-charging, or DO-178C/DO-254-level
  software/hardware assurance on flight-critical power electronics — those
  remain comparatively less mature areas even where the basic "is an
  electric powertrain certifiable" question has been answered.

## Gaps this document does not cover

Add primary sources (EASA TCDS A.573, any published certification review
items, NTSB/EASA incident reports if applicable) if deeper detail is needed
for a specific Stage 3 assessment.
