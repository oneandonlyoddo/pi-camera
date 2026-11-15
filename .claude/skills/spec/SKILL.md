---
name: spec
description: Plan a future feature in conversation with the user, without implementing anything. Bounce ideas, ask about preferences, check them against the specs and rules, and record every decision in a spec file under docs/specs/ that /feature can implement later. Use when the user wants to plan, discuss, spec or think through a feature ("let's plan X", "spec out Y", "I want to think about Z for later").
argument-hint: "<feature idea or existing spec name>"
---

# Spec workflow (no implementation)

**Hard limit:** this skill writes only `docs/specs/<slug>.md` and, at the end, one row in `docs/FEATURES.md`. No code, tests, assets, other docs, no `dev.sh`, no commits. Other features may be half-done in the working tree; don't touch or "fix" them. If the conversation finds a bug, note it in the spec under Notes and tell the user; don't fix it.

## 1. Start or resume

- `docs/specs/<slug>.md` exists → read it, summarise decisions and open questions, continue from there.
- New → read `docs/FEATURES.md`.
  - Under **Rejected** → say so and why. Continue only if the user overrules it.
  - Already `done`/`wip` → say so; the spec is then a change to it.
- Read what the idea touches: `docs/SPECS.md` (capture, display, GPIO, touch, timing, memory, storage), `docs/design/hud.md` / `docs/design/web.md` (UI), `.claude/rules/`, and the code involved, read-only. Know the real constraints before proposing.
- Create the spec file from the template below with status `draft`, and fill in what the user already said.

## 2. Conversation

Go back and forth until the user says it's final. Each turn:

- Ask a few focused questions (not a questionnaire). Use AskUserQuestion when there are clear options; offer a recommendation and say why.
- Bring in what the user may not see: hardware limits (512 MB, slow CPU, capture time), rule conflicts (R1 apt-only, R2 threads, R6 budget, R7 web input, R11 photos), interaction with existing features, cheaper alternatives, and things to leave out.
- Push back on ideas that don't fit the constraints; offer the closest one that does.
- After each decision, update the spec file at once (decision + one-line why), so nothing lives only in the chat. Move answered items out of Open questions.

The user's preference decides. Record their choice even when you recommended otherwise, with their reason.

## 3. Finalise

When the user says it's final:

- No open questions left (or each one explicitly deferred with who decides and when).
- Requirements are concrete enough that `/feature` needs no further design choice: values, ranges, defaults, UI placement, naming, error behaviour.
- Set status `final`, date it.
- Add or update the row in `docs/FEATURES.md`: status `planned`, Notes `spec: docs/specs/<slug>.md`. A rejected idea → move it to **Rejected** with the reason instead, and set the spec status `rejected`.
- Show the user the finished spec in short form.

To implement later: `/feature docs/specs/<slug>.md`.

## Template

```markdown
# <Feature name>

Status: draft | final | rejected · Updated: YYYY-MM-DD

## Goal
What the user gets, in 1–3 sentences.

## Decisions
- **<topic>:** <choice>. Why: <reason>.

## Requirements
Numbered, testable. What it does, values/ranges/defaults, UI (HUD / touch menu / web), persistence, errors.

## Out of scope
What it deliberately does not do (and why, if not obvious).

## Constraints and risks
Rules (R-IDs), SPECS targets it can affect (shot-to-shot, memory, boot), dependencies (apt package or none), interaction with other features.

## Verification
What `/on-device` can check, and what needs a person at the device.

## Open questions
- <question> (options, recommendation)

## Notes
References, sample images, rejected alternatives with reasons.
```
