# Keats Deck — Revisions for Gamma

**Two decisions first:** (1) This deck is 6 slides counting title/thank-you,
not 3-5 — fold the closer into slide 5 or decide bookends don't count. (2)
Name the gaps below proactively rather than waiting for Q&A — it reads as
"I already found this."

**Slide 1 (Title).** Swap "grounded in live data" → "grounded in a real
tool call against order data." "Live" overclaims a mocked backend.

**Slide 2 (Architecture), step 4.** Swap "hit verified data sources —
orders, accounts, policy configs" → "hit a mocked order database — no live
accounts or policy systems yet." "Accounts" doesn't exist in the code at
all.

**Slide 3 (Principles).** Scope "Always Look Up, Never Guess" to order data
only — general policy questions are answered directly, not tool-verified,
per the agent's own rules. Add a 4th card: "Chat by Design" — voice was out
of scope this round, not overlooked.

**Slide 4 (Auditable/Configurable/Cost).**
- "No engineering dependency for rule changes" → add: this build reloads
  on restart; live hot-reload is the next lift.
- "Cost scales predictably" → add a real number: ~$0.01-0.03 per
  conversation at Sonnet 4.5 pricing.
- "Compliance is structural, not bolted on" → "Built early, verified by 18
  automated checks." (Safer than a claim your own commit history
  contradicts.)

**Slide 5 (Path Forward).**
- "Retries built in" → add: "and idempotency, so a retry can't double-file
  a return."
- Add a line (slide or speaker notes): operational monitoring — latency,
  error rate — is a separate gap from audit logging, still open.
- Core Claim → "Keats never guesses on order-specific facts and never acts
  unilaterally. Out-of-scope requests get a handoff, not an improvised
  answer." This scopes "never guesses" accurately and finally shows what
  "wrong gracefully" means.

**Edit note:** these are direct text swaps, no layout changes except the
new slide-3 card. Read slides 1 and 5 back to back after editing — they
should sound like one consistent level of confidence, not two.
