# Provenance — read this before drawing any conclusion

This document states exactly what is real and what is synthetic in this
worked example. Hard honesty is the point: the artifact is worthless if its
provenance is fuzzy.

## What is real

- `action_ref` is derived exactly per `action-ref-v1`
  ([argentum-core/docs/spec/action-ref.md](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)):
  SHA-256 of the RFC 8785 JCS canonicalization of the four preimage fields
  (`agent_id`, `action_type`, `scope`, `timestamp`). The value in
  `artifacts/manifest.json` was independently cross-checked against
  argentum-core's own reference implementation
  (`plugins/agt_evidence_anchor/action_ref.py`,
  `compute_action_ref()`) and matches byte-for-byte.
- The request/response shapes are modeled on market.near.ai's own public
  documentation, fetched and read in full before any code was written:
  - [`/skill/SKILL.md`](https://market.near.ai/skill/SKILL.md) — the worker
    skill: `POST /v1/assignments/{id}/submit`, the golden path, the hard
    rules (`deliverableMarkdown` ≤ 256 KiB is the result itself).
  - [`/skill/reference/agent-api.md`](https://market.near.ai/skill/reference/agent-api.md),
    "Deliverable rules (REST submit)" — the one sentence that exists for
    `deliverableHash`: `deliverableMarkdown` is "stored and **hashed by the
    platform**", nothing more.
  - [`/openapi.json`](https://market.near.ai/openapi.json) —
    `components.schemas.SubmitRequest` (required: `deliverableMarkdown`;
    optional: `files`) and `components.schemas.DeliverableVersionView`
    (required: `version`, `files`, `submittedAt`; optional:
    `deliverableHash`, `deliverableUrl`, `senderAgentId`) were read directly
    from the live schema, not inferred.
- The on-chain anchor is a real transaction on Base mainnet, sent via
  `giskard-signer` (owner wallet, policy-gated, key never touched by this
  session): tx `0x127a8e1ff40beee2df0cc0471f551c52adcf7e30d44bd9fb10ee39de50de561e`,
  block `52605019`, `status: 0x1 (success)`. The tx hash and block are
  independently checkable by anyone via `verifier/verify.py`, which was run
  and produced `ALL CHECKS PASS` against public Base RPC
  (`base-rpc.publicnode.com` — deliberately a *different* node than the one
  `giskard-signer` used to broadcast, so the verification does not just
  re-ask the same server that sent the transaction) after the transaction
  confirmed.

## The real gap this responds to — precise, not inflated

market.near.ai's Agents Marketplace is in active production (per its own
`llms.txt`: 1,284 agents, 42,118 jobs in the week fetched, $1.2M paid to
builders, 96.4% success rate). Every delivery goes through
`POST /v1/assignments/{id}/submit` (`deliverableMarkdown` + optional
`files`), and if the buyer never reacts, `autoAcceptAt` releases escrow on
silence (`/skill/SKILL.md`, "Hard rules" #4).

**This is not "no hash exists."** `deliverableHash` is a real field,
present in the live OpenAPI schema on both `JobAssignment` and
`DeliverableVersionView`. What IS real, verified by reading the schema and
every prose reference to the field directly (not inferred, not assumed):

- `deliverableHash` has **no description anywhere in the OpenAPI schema** —
  every other field on the same objects does.
- It is named exactly **once** across all of `SKILL.md`,
  `reference/agent-api.md`, and `reference/webhooks.md`: "stored and hashed
  by the platform." No algorithm is stated. No stated preimage beyond
  `deliverableMarkdown` — the prose does not say whether `files` are
  covered, and nothing in the schema says either.
- It is **absent from `SubmitRequest`** — the worker never supplies it, and
  the live schema gives no way for a worker or buyer to know in advance
  what value to expect back.
- It carries **no signature** of any kind. The only signature this API
  documents anywhere is `X-Market-Signature` on outbound **webhooks**
  (`reference/webhooks.md`: `sha256=<hex HMAC-SHA256(secret, "<timestamp>.
  <raw body>")>`) — an HMAC over the webhook *delivery*, keyed to a shared
  secret between the platform and one registered agent. It authenticates
  that a webhook came from the platform; it says nothing about binding a
  specific deliverable to a specific awarded assignment in a way a third
  party (the buyer, an auditor, anyone without that shared secret) could
  check.
- Nothing connects `deliverableHash` to `assignmentId`, `jobId`,
  `workerAgentId`, or the award itself (`escrowAmount`/`escrowToken`) —
  it is a bare, undocumented string next to the deliverable, not a
  commitment over the assignment.

So the honest statement of the gap is narrower and more precise than "zero
integrity data exists": **an undocumented, unsigned, unscoped internal hash
exists; nothing public commits the specific delivered content to the
specific awarded assignment in a way an independent third party —
including the buyer who is about to have `autoAcceptAt` release funds on
their silence — can verify without trusting the platform's own storage
layer.** `action_ref` (content-addressed over `agent_id`, `action_type`, a
`scope` string carrying `assignmentId` and the deliverable's own content
hash, and `timestamp`) is exactly the kind of public, recomputable,
third-party-checkable commitment this gap is missing — independent of
whether `deliverableHash`'s own undisclosed algorithm is ever published.

**`deliverableHash` in `artifacts/manifest.json`'s `result` block is an
assumption this worked example makes explicit, not a captured real value**:
it is computed here as plain SHA-256 of `deliverableMarkdown` alone
(`verifier/verify.py`'s `deliverableHash (as assumed)` check recomputes
exactly that and nothing more) — the one reading consistent with the
single sentence market.near.ai's own docs give it. The real platform may
hash something else entirely (different algorithm, different encoding,
files included); that is precisely the ambiguity this worked example is
naming, not resolving.

## What is synthetic — declared

- **No running worker agent, real marketplace account, or real
  assignment, job, or escrow payment was involved.** `assignmentId`,
  `jobId`, `workerAgentId`, `deliverableMarkdown`'s content, and the file
  URL are all constructed in `scripts/produce.py` — nothing here was
  submitted to market.near.ai's actual API, and no real escrow was funded
  or released.
- **`assignmentId`, `jobId`, `workerAgentId`, and the file URL are
  obviously-synthetic placeholders** (`018f3b2e-7a4d-7c91-9e2a-worked-
  example-*`, a `/files/WORKED-EXAMPLE-TOKEN/...` link that resolves to
  nothing real).
- `escrowAmount`/`escrowToken`/`slaDeadlineAt`/`acceptanceWindowDays` are
  plausible values in the schema's own documented ranges, not real
  marketplace data.

## What this therefore does and does not show

- **Does show:** the `action_ref` derivation applies unchanged to
  market.near.ai's own documented `submit` call shape — same four fields,
  same JCS + SHA-256 path used by every other emitter in this series
  (Keycard, Turnkey, Binance, OKX, pay-kit, MachineFi, Kraken, Coinbase,
  Polygon, r0x, WDK, PayPal, Fireblocks, agent-bounties, Cashu). It also
  names a real, precise ambiguity in a production system with real
  volume: an undocumented hash field next to an auto-accept clock that
  releases real money on silence.
- **Does not show:** that market.near.ai or NEAR AI has integrated,
  endorsed, or adopted `action_ref`, or that `deliverableHash` is broken,
  insecure, or exploited today — only that its contract is unpublished.
  No claim of "NEAR AI integrated us," no claim of on-chain adoption. If
  someone reads it as adoption, that reading is wrong.
