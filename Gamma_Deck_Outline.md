# Keats — Bookly's Support Agent — Pitch Deck Outline (for Gamma)
Decagon SE Take-Home | 5 slides

Design approach: each slide leads with an assertive, single-idea headline
(a claim, not a topic label) per Duarte's S.P.A. method — Simplify the
content down to one idea, Plan the headline as a point of view, and
Accentuate with one deliberate visual rather than decoration. Slides carry
the claim; the speaker notes carry the explanation, so nothing sounds like
it's being read off the screen live.

---

## Slide 1 — Title

**Headline:** Verify Before You Speak. Confirm Before You Act.

**Subhead:** Meet Keats — Bookly's AI support agent, and the argument for
why it's built this way.

**On-slide content:** headline, subhead, and a small credit line ("Decagon
SE Take-Home | [Your Name]"). The name "Keats" appears here and nowhere
else needs to introduce it again — one clean reveal, not a running bit.

**Visual:** Full-bleed dark background, the Keats logo centered above the
headline — this is the one slide where the logo does real work instead of
sitting in a corner as a watermark.

**Speaker notes:** This is the thesis, stated as the title, not buried in
paragraph three. A good CX agent should never guess when it can verify, and
never act when it should ask first. The name is a small, deliberate choice
in the same spirit: a support agent customers address by name reads as
accountable — a "who," not a chatbot — which is the same trust argument the
rest of this deck makes about its behavior. Keep this line in your back
pocket rather than over-explaining it; the name should feel obvious once
said once, not defended.

---

## Slide 2 — Architecture

**Headline:** Every Answer Passes Through a Tool Call First

**On-slide content:** one horizontal flow, five steps, no paragraph text:
Customer message → Orchestrator (Claude + tools) → Decide: answer / clarify
/ call tool → Mocked backend → Response. One line beneath it: "The loop
repeats — tool results feed back before the agent responds."

**Visual:** The five-box flow diagram (reuse the color-blocked flow from
the existing deck if it's on-brand); no bullet list competing with it.

**Speaker notes:** Four components do the real work: orchestration (Claude's
tool-use loop decides per turn), tools (get_order_status,
check_return_eligibility, initiate_return, lookup_orders_by_email), prompts
(now loaded from agent_policies.md, not hardcoded — see slide 4), and memory
(the running message list, session-only, no persistence yet).

---

## Slide 3 — Key Decisions

**Headline:** Three Bets, One Throughline: Never Guess

**On-slide content:** three tight columns, icon + 3-4 words each, not full
sentences:
1. Tool-calling over prompt-only reasoning — "No answer without a lookup"
2. Confirm-then-act on returns — "No action without a 'yes'"
3. Mocked backend, not a live API — "Isolate judgment from plumbing"

**Visual:** Three equal-weight cards or columns, one icon each, heavy on
whitespace — resist the urge to add the full tradeoff paragraph on the
slide itself.

**Speaker notes:** For each — what I chose, what I traded off, why it was
worth it. (1) Tool-calling: the model can't answer from memory, full stop;
trades some conversational flexibility for eliminating the single biggest
trust-killer in CX agents — a confident, wrong answer. (2) Confirm-then-act:
one extra turn of friction on every return, in exchange for never letting
the agent take an irreversible action on a misread request. (3) Mocked
backend: doesn't prove real API resilience, but isolates the orchestration
logic being evaluated from integration plumbing that's a known quantity.

---

## Slide 4 — What I Changed After Review

**Headline:** I Found the Gap Myself, Then Closed It

**On-slide content:** four short callouts, not paragraphs:
- Identity check — a real order ID + wrong email = not found, same as a
  fake order ID
- Policy file, not hardcoded rules — agent_policies.md is the AOP-style
  config a CX ops person could edit directly, no engineering ticket
- Cost visibility — live mode prints estimated cost per conversation
- Audit trail — every tool call logged, emails hashed, never stored raw

**Visual:** Four small icon-labeled blocks in a single row or 2x2 grid —
this is the "proof of iteration" slide, so let the four items read like a
punch list, not an essay.

**Speaker notes:** The first version of this worked but had a real gap —
any order ID would return data regardless of who was asking. I went back
and fixed it rather than leaving it as a bullet under "future work," and
used that same pass to close three more gaps a reviewer would ask about:
where the agent's rules actually live (this is where I'd point to Decagon's
own Agent Operating Procedures pattern — my hardcoded rules were the
opposite of that, so I externalized them), what this costs to run, and how
it'd hold up to an audit. This slide is the evidence that the thesis
("verify before you speak, confirm before you act") applies to how I work,
not just what the agent does.

---

## Slide 5 — What's Next / Close

**Headline:** The Roadmap From Prototype to Production

**On-slide content:** three items, in priority order, each one line:
1. Real authentication, not just an email match
2. Live order-management API, with retries
3. Human escalation path for low-confidence cases

**Visual:** Simple numbered list treatment, generous whitespace, maybe a
subtle upward path/arrow motif tying back to "production." Close on a
one-line sign-off: "Happy to walk through the code and defend any of this
live."

**Speaker notes:** Also worth having ready but not on the slide: known,
deliberate exclusions (exchanges, partial refunds, gift returns, non-English
support, voice) and the honest limitation that the test suite covers tool
logic, not full conversational behavior — LLM behavior isn't unit-testable
the same way rule-based code is.

---

### Notes for building this in Gamma

- Paste each slide's Headline + on-slide content as its own section; Gamma
  will treat the headline as the slide title if you keep it short and
  declarative (avoid punctuation-heavy topic labels like "Architecture:
  System Overview").
- Keep the "on-slide content" lines as the only visible text — the speaker
  notes are for you to say live or add to Gamma's speaker notes field, not
  to put on the slide itself. This is the single biggest lever for making
  it look designed rather than templated.
- If Gamma's auto-layout defaults to bullet lists, override columns/cards
  for slides 3 and 4 specifically — those two are built to be scanned as
  parallel items, not read top to bottom.
