---
name: ama
description: >-
  Ask-me-anything interview. Relentlessly question a plan, idea, or
  design until we reach shared understanding, resolving each branch of the
  decision tree. Use when the user says "ama", "ask me anything", or wants to be
  interviewed about a plan.
---

Interview me relentlessly about every aspect of this plan until we reach a
shared understanding. Before starting make sure you have a good idea of the
questions you want to ask and lay them out to the user, only then start going
through the decision tree. Walk the decision tree depth-first — finish a branch
before opening another.

Use the AskUserQuestion tool for every question. One decision per call. Offer
2–4 concrete options and mark your recommended one with a one-sentence
rationale. Never bundle unrelated decisions into a single call.

Before asking me anything that could be answered from the codebase or files,
delegate a read-only lookup to the `basic-explorer` subagent and use its
findings instead of asking. Keep exploration out of this conversation's context.

Push back on answers that are vague, risky, or inconsistent with something I
said earlier.

When every branch is resolved, stop and summarise the locked-in decisions.