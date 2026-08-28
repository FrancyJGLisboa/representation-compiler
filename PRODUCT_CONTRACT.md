# Product Contract

## Purpose

Representation Compiler helps a person find the representation of a subject that lets them understand, reason about, explain, and act on it.

## Primary objective

Optimize for **understanding utility**:

- accurate explanation in the user's own words;
- transfer to a related question or scenario;
- explicit uncertainty, disagreement, and evidence;
- lower cognitive load without discarding relevant structure.

## Downstream tasks

Decision support, project tracking, teaching, research, and team alignment are downstream applications of understanding—not separate product cores.

## First serious wedge: astronomy representation notebooks

The first domain-specific product is an astronomy representation notebook: a shareable object that records a dataset, coordinate frames, mappings between representations, preserved/discarded information, scientific claims, interactive controls, and executable tests.

An astronomer should be able to publish a representation that another person can inspect, change, test, fork, and cite—not merely a diagram or a chat transcript. The first executable invariant is an ICRS right-ascension/declination to Cartesian unit-vector transformation; later slices add FITS/table ingestion, units, uncertainty propagation, coordinate-frame transforms, and interactive views.

## Invariants

- The system searches structurally different representations before selecting one.
- A visual is a projection of evidence-backed reality, not the record of truth.
- A person can say which representation clicked and why.
- Candidate representations include what they preserve, discard, and a falsification test.
- A published scientific representation records its data provenance, coordinate frame, mapping, assumptions, and executable checks.
