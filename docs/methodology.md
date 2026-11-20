# Methodology

## Scope

The benchmark evaluates factual accuracy, hallucination, bias, safety, and
language understanding in Sinhala (`si`) and Tamil (`ta`). Each task should
specify its category, evaluation method, evidence requirements, and scoring
rules before model comparisons begin.

## Experimental controls

Record benchmark and prompt versions, model name and version, generation
configuration, random seed, runtime/software versions, and source revision.
Separate development data from the private held-out test split. Do not select
models or tune prompts using test outcomes.

## Reporting

Retain per-question outputs and explicit failures. Report denominators,
uncertainty, relevant subgroup results, and any exclusions. Use paired
comparisons where appropriate and account for multiple comparisons when testing
many models or metrics. Human-reviewed labels remain the basis for validation;
LLM-judge outputs are supplementary.

## Status

This document describes intended practice, not a finalized protocol. Update it
with concrete scoring rubrics and statistical decisions before publishing
benchmark results.
