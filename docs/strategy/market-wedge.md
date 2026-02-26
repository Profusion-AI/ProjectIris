# Market Wedge (MVP)

Date: 2026-02-26
Owner: Kyle
Support: Codex

## Target Customer (Initial)
Cloud and edge teams shipping interactive video or AI-in-the-loop streaming features where transport latency is a product KPI.

## Core Problem
Existing stacks force a tradeoff between low-latency real-time delivery and stable buffered delivery, with weak visibility into transport behavior under production-like load.

## Iris Wedge
- Tunable transport behavior (`real-time` vs `buffered`) with evidence-backed session artifacts.
- Operator-friendly control plane surface for orchestrating and measuring session quality.
- Lightweight embeddable web player path for integration validation.

## First Paid Use-Case Hypothesis
A team running premium real-time experiences pays for managed deployment, SLO visibility, and integration support once Iris demonstrates lower latency variance with acceptable reliability versus their baseline pipeline.

## Immediate Validation Plan
1. Interview 5 candidate teams (cloud gaming, telepresence, AI video).
2. Collect baseline latency + jitter pain metrics.
3. Run one side-by-side proof using Iris evidence artifacts.
4. Convert strongest use case into a priced pilot offer.
