---
name: popular-science-video-script
description: Use when creating, revising, or reviewing educational explainer video scripts, especially Quarto revealjs video-lesson-slides with narration. This skill adapts science communication, multimedia learning, and visual-first scripting principles for public-facing or learner-facing explanatory videos; use alongside AEA when slides need sentence-claim headlines and alongside academic-writing-cohesion when narration needs smoother flow.
---

# Popular Science Video Script

## Overview

Create and revise educational explainer videos as visual-first stories, not as ordinary slide decks. The goal is to help a learner understand one idea at a time through a tight loop of curiosity, visual evidence, spoken explanation, and consequence.

Use this skill for `video-lesson-slides.qmd`, narration notes, scene outlines, slide-to-voice alignment, or reviews of public-facing technical course videos.

## Relationship to Other Skills

- Use `aea-presentation` as a supporting constraint: content-slide headlines should still make clear sentence claims supported by evidence.
- Use this skill to decide video pacing, hooks, scene sequence, narration style, and visual treatment.
- Use `academic-writing-cohesion` when paragraphs or speaker notes feel choppy, jumpy, or hard to follow.

## Core Principles

- Start from the audience's question, not the source material's table of contents.
- Write to visuals: every spoken segment should have a clear visual job.
- Prefer one teachable turn per scene: reveal a problem, show a mechanism, correct a misconception, or connect a consequence.
- Open with a concrete hook: a contradiction, failure case, surprising comparison, or visual that makes the lesson worth watching.
- Avoid front-loaded background. Give context only when the viewer needs it to interpret the current visual.
- Make the script sound spoken. Use short sentences, explicit referents, and conversational transitions.
- Keep technical accuracy visible. Simplify the route to the idea, not the idea itself.
- Replace decorative slides with evidence-bearing visuals: diagrams, timelines, decision paths, annotated charts, structured comparisons, or concrete examples.
- Treat on-screen text as labels and anchors, not as the narration transcript.
- Close loops. If a scene raises a question, answer it before moving on or deliberately carry it forward.

## Scene Template

For each scene or slide, specify:

- `audience_question`: what the learner is wondering at this moment.
- `hook_or_turn`: the curiosity, contrast, misconception, or risk that moves the scene.
- `claim`: the one sentence the viewer should remember.
- `visual_job`: what the image, table, chart, or diagram must show.
- `narration`: spoken explanation that interprets the visual without reading it.
- `onscreen_text`: only the labels, numbers, or short phrases needed to follow the visual.
- `technical_guardrail`: the accuracy constraint that must not be lost.
- `transition`: why the next scene naturally follows.

## Workflow

1. Define the learner: prior knowledge, likely misconception, and reason to care.
2. Reduce the lesson to a single promise: after this video, the learner can explain or recognize one important thing.
3. Draft a curiosity path before drafting slides:
   - hook
   - first simple model
   - complication or pitfall
   - corrected model
   - practical consequence
   - recap
4. Build the visual sequence. Each scene needs a visual reason to exist.
5. Draft narration against the visual sequence, using spoken language and clear sentence chaining.
6. Add AEA-style headlines after the story path is clear.
7. Audit pacing: remove background, caveats, and definitions that do not help the current scene.
8. Verify technical fidelity against the book or source material before finalizing.

## Explainer Patterns

Use the pattern that best fits the concept:

- **Failure-first**: show a plausible mistake, then explain the hidden assumption. Good for pitfalls, biases, backtesting errors, and debugging.
- **Timeline reveal**: show what is known when, then reveal why later information cannot be used earlier. Good for look-ahead bias and execution timing.
- **Before/after model**: show the naive model, then the corrected model. Good for price adjustments, venue assumptions, and transaction costs.
- **Mechanism walk-through**: follow one order, signal, data point, or trade through the system. Good for execution logic and data pipelines.
- **Comparison table**: contrast two worlds with the same rows. Good when the lesson is about mismatched assumptions.
- **Concrete-to-general**: start with one example, then name the principle. Good for abstract statistical or methodological ideas.

## Narration Style

- Use direct, concrete verbs: `uses`, `knows`, `trades`, `fills`, `fails`, `inflates`.
- Keep most spoken sentences under 20 words.
- Prefer `this signal`, `this price`, `this database`, or `that order` over vague `this` or `it`.
- Use signposts sparingly: `Here is the catch`, `The timing matters`, `Now the backtest is cheating`.
- Let the audience feel the problem before naming the technical term.
- Explain jargon immediately after using it, or delay the term until the viewer has seen the phenomenon.
- Use analogies only when they preserve the technical relationship. Drop analogies that add a second thing to explain.

## Visual Rules

- The first visible scene should create orientation or curiosity within seconds.
- Visuals must carry information: a viewer should understand the core claim even with the audio muted.
- Use motion or progressive reveal when the concept is temporal, causal, or procedural.
- Use labels at the point of need, close to the relevant visual element.
- Avoid duplicating narration as full sentences on screen.
- Prefer stable recurring visual vocabulary across a chapter: same color for live trading, backtest, unavailable information, and invalid assumptions.
- If the source is a table, consider whether a diagram, timeline, or annotated path would explain the relationship better.

## Review Checklist

- Does the opening create a reason to keep watching?
- Can every scene answer: why this visual, why now, and why does it matter?
- Is there exactly one main claim per slide or scene?
- Does the narration interpret the visual instead of reading it?
- Are definitions introduced after the viewer has a concrete need for them?
- Are caveats preserved without derailing the main explanation?
- Does the sequence move from concrete example to transferable principle?
- Would a learner know what mistake to avoid or what decision to make after the video?
- Are notes faithful to the book or source material?

## Output Expectations

When creating or revising a video lesson, return practical artifacts:

- revised slide headlines
- scene-by-scene outline
- narration notes
- visual concepts or figure briefs
- specific cuts or rewrites
- technical guardrails and source-faithfulness checks

Prefer concrete rewrites over generic advice.
