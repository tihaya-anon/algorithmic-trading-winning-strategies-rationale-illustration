---
name: academic-writing-cohesion
description: This skill should be used when revising, diagnosing, or teaching academic writing flow and cohesion, including known-new order, sentence chaining, paragraph coherence, key-term repetition, pronoun reference, transitions, signposting, and parallel structure.
---

# Academic Writing Cohesion

## Overview

Revise academic prose so that readers can follow the argument without guessing how sentences and paragraphs connect. Focus on known-new order, sentence chaining, paragraph architecture, stable terminology, clear pronoun reference, precise transitions, signposting, and parallel structure.

Load `references/cohesion-method.md` when the task asks for detailed diagnosis, source-backed explanation, teaching, paragraph-level revision, or a before/after critique.

## Trigger Conditions

Use this skill when the user asks to:

- Improve academic writing flow, cohesion, coherence, readability, or paragraph logic.
- Rewrite paragraphs using known-new, old-to-new, given-new, or chain-method principles.
- Diagnose why a paragraph feels choppy, jumpy, repetitive, vague, or disconnected.
- Fix topic sentences, paragraph endings, transitions, signposting, key-term repetition, or pronoun reference.
- Review literature reviews, introductions, method sections, results, discussion sections, essays, grant text, or technical prose for reader guidance.
- Teach or explain academic writing cohesion techniques.

## Core Rules

Apply these rules by default:

- Preserve meaning, technical terms, citations, hedging, and disciplinary nuance.
- Put familiar information before new information when possible.
- Let the end of one sentence prepare the start of the next sentence.
- Repeat key terms when precision matters; avoid unnecessary synonym swapping.
- Clarify vague demonstratives such as `this`, `it`, `they`, and `these`.
- Use transitions only when they accurately signal the logical relation.
- Keep each paragraph anchored to one controlling idea.
- Use parallel sentence structure for parallel claims.
- Prefer reordering, explicit reference, and clearer topic structure over superficial polishing.

## Workflow

1. Identify the passage type, audience, and revision goal.
2. Determine each paragraph's main claim or function.
3. Map the sentence chain: old information, new information, and link to the next sentence.
4. Identify breaks: abrupt topic shifts, vague pronouns, unstable terms, missing transitions, overused transitions, weak topic sentences, or unsupported sentences.
5. Revise sentence order and syntax so known information leads into new information.
6. Repair paragraph structure with a clear topic sentence, support sequence, and closing or linking sentence.
7. Preserve the author's claims and evidence while reducing reader effort.
8. Return the revision with concise notes explaining the highest-impact cohesion changes.

## Revision Modes

Choose the output mode that fits the user's request:

- `direct rewrite`: provide a polished revised passage with minimal explanation.
- `diagnostic review`: list cohesion problems and concrete fixes before rewriting.
- `teaching mode`: explain the principle, show before/after examples, and name the technique used.
- `tracked rationale`: provide the revised passage plus bullet notes on known-new order, sentence chaining, reference, transitions, and paragraph coherence.

## Known-New Pass

For each sentence:

1. Move familiar material, repeated key terms, or the previous sentence's result toward the beginning.
2. Move the new claim, contrast, consequence, or emphasis toward the end.
3. Start the next sentence from that new material when the paragraph continues the same line of thought.
4. Add a short bridge when the relationship is not inferable.

Avoid mechanical rewriting. Preserve emphasis when the author's rhetorical goal requires fronting new or surprising information.

## Paragraph Coherence Pass

Review each paragraph as a unit:

- State the paragraph's main point in one sentence.
- Check whether the first sentence or early sentences announce that point.
- Remove or relocate sentences that do not support, qualify, exemplify, contrast with, or extend the point.
- Add a final sentence when the paragraph needs closure or a bridge to the next paragraph.
- Split a paragraph when two controlling ideas compete.

## Feedback Style

When giving feedback, make it concrete:

- Quote or identify the problematic phrase or sentence.
- Name the cohesion issue.
- Provide a revised version.
- Explain the logic in one sentence.

Avoid vague comments such as "improve flow" unless followed by a specific diagnosis and rewrite.
