# ADR-0001: Dual license for data and code

## Status

Accepted

## Context

This repository publishes a public internship dataset (`data/`) alongside
automation and documentation. A single license would either over-restrict
code reuse or under-protect dataset attribution.

## Decision

- Dataset files under `data/` are **CC-BY 4.0** ([LICENSE-DATA.md](../../LICENSE-DATA.md)).
- All other files are **MIT** ([LICENSE.md](../../LICENSE.md)).
- [NOTICE](../../NOTICE) summarizes the split.

## Consequences

- Redistributors of catalog JSON must attribute the dataset per CC-BY 4.0.
- Scripts, tests, configuration, and docs can be reused under MIT terms.
- Public README footer documents both licenses.
