# nearai-agents-market-action-ref-anchor

A worked example that derives an **`action_ref`** — a deterministic,
content-addressed identifier for an agent action
([`action-ref-v1`](https://github.com/giskard09/argentum-core/blob/master/docs/spec/action-ref.md)) —
for a synthetic worker `submit` on [market.near.ai](https://market.near.ai)
(NEAR AI's Agents Marketplace, in active production: 1,284 agents, 42,118
jobs/week, $1.2M paid to builders per its own public `llms.txt`), and
anchors it permissionlessly on-chain, giving it a property the call does
not have on its own: an **externally verifiable, third-party-checkable
record of what was delivered and when**, independent of the platform's own
storage.

> **Provenance, up front (read `PROVENANCE.md` for the full statement).**
> The `action_ref` here is derived exactly per `action-ref-v1` and
> cross-checked against argentum-core's own reference implementation. The
> request/result shapes are modeled on market.near.ai's **public
> documentation** (`/skill/SKILL.md`, `/skill/reference/agent-api.md`,
> `/openapi.json`) — but it was **NOT produced by a live worker agent or a
> real marketplace account**: no real assignment, job, or escrow payment.
> All identifiers are obviously-synthetic placeholders. Nothing here — on-
> chain or in this repo — implies that market.near.ai or NEAR AI
> integrated, endorsed, or participated.

## Why this, precisely

market.near.ai documents `deliverableHash` as a real field on both
`JobAssignment` and `DeliverableVersionView` — but it has no description
anywhere in the live OpenAPI schema, is named exactly once in prose
("stored and **hashed by the platform**", no algorithm stated), is absent
from the submit request itself, carries no signature, and is not bound to
the assignment, job, or escrow it belongs to. The only documented signature
anywhere in the API (`X-Market-Signature`, HMAC-SHA256) authenticates
outbound webhook *delivery* to one registered agent — it says nothing about
binding a delivered artifact to its award for a third party (the buyer
about to have `autoAcceptAt` release funds on silence, an auditor, anyone
without the webhook secret) to check. See `PROVENANCE.md` for the exact
reading of every public reference to the field, verified against the live
schema and docs, not assumed.

## The idea

The `submit` request's own documented interface (`/openapi.json`,
`SubmitRequest`: `deliverableMarkdown`, `files`) and the assignment's own
fields (`JobAssignment`: `assignmentId`, `jobId`, `workerAgentId`,
`escrowAmount`, `slaDeadlineAt`) are declared, checkable facts about one
delivery. `action_ref` closes part of the gap above: a content-addressed
identifier any party can recompute from four declared fields (`agent_id`,
`action_type`, `scope`, `timestamp`) — no trust in the platform's storage
layer required. This repo's `scope` carries the assignment id and the
deliverable's own SHA-256 directly (`nearai:agents-market:v1/assignments/
{id}/submit:assignment:<id>:deliverable_sha256:<hash>`), and the envelope
adds `params_digest`/`result_digest` — hashes of the exact declared
request/response context, independently recomputable from the JSON alone.

```
   market.near.ai `submit` call                 public chain (Base)
   ┌───────────────────────────┐            ┌────────────────────────┐
   │ agent_id, action_type,     │  JCS+SHA256│ AnchorRegistry         │
   │ scope (assignment+hash),   │───────────▶│  anchor(bytes32 ref)   │
   │ timestamp (submittedAt)    │  action_ref│  Anchored(ref,by,time) │
   │ + params/result digests    │            └────────────────────────┘
   └───────────────────────────┘             operator-independent
        deliverableHash: undocumented,       timestamp / finality
        unsigned, unscoped (see PROVENANCE)
```

## Doctrine: spec-agnostic to market.near.ai's format

We derive `action_ref` from the four canonical fields only. We do **not**
ask NEAR AI or agents-market to adopt any anchoring infrastructure, change
their API, or emit any new fields. The integration lives entirely in how a
`submit` call *could* be shaped and anchored; the platform's documented
source is the input, the anchor is the added property.

## What's here

| Path | What it is |
|------|-----------|
| `scripts/produce.py` | Derives `action_ref` per `action-ref-v1` (JCS RFC 8785 + SHA-256) for a synthetic worker `submit`, plus the `params_digest`/`result_digest` envelope. |
| `verifier/verify.py` | Independent (stdlib-only) verifier: recomputes both digests from the declared JSON, recomputes `deliverableHash` under the one reading market.near.ai's own docs state, and confirms the matching `Anchored` event on Base mainnet. |
| `artifacts/` | The canonical instance: `manifest.json` (preimage, digests, envelope) and `anchor.json` (tx/block, once anchored). |
| `scripts/anchor.sh` | The `cast`-equivalent call for the same anchor (this repo's own anchor was sent via `giskard-signer`, see `PROVENANCE.md`). |
| `PROVENANCE.md` | Exactly what is and isn't real about this artifact, and the precise (not inflated) statement of the `deliverableHash` gap. Read it. |

## Reproduce

```bash
# 1. derive action_ref + the envelope digests
python3 scripts/produce.py artifacts

# 2. anchor action_ref on Base mainnet (see scripts/anchor.sh)

# 3. independently verify the derivation and the on-chain anchor
python3 verifier/verify.py
```

## The anchor

- **Registry:** `0x49fEcA52bC634a9Ab773226D16619deC547794aa` (same CREATE2
  address on Base 8453, Arbitrum One 42161, Ink 57073).
- **Function:** `anchor(bytes32 ref)` — permissionless, no owner/roles/funds.
- **Event:** `Anchored(bytes32 indexed ref, address indexed anchoredBy, uint256 timestamp)`.
- Tx `0x127a8e1ff40beee2df0cc0471f551c52adcf7e30d44bd9fb10ee39de50de561e`,
  block `52605019`, Base mainnet. `artifacts/anchor.json` has the full
  record; `verifier/verify.py` confirms it independently against public RPC
  (verified against `base-rpc.publicnode.com`, deliberately a different
  node than the one that broadcast the transaction).

## Related worked examples

Same pattern, other formats: [`okx-agent-payments-action-ref-anchor`](https://github.com/giskard09/okx-agent-payments-action-ref-anchor)
(OKX), [`binance-onchain-pay-action-ref-anchor`](https://github.com/giskard09/binance-onchain-pay-action-ref-anchor)
(Binance), [`kraken-order-action-ref-anchor`](https://github.com/giskard09/kraken-order-action-ref-anchor)
(Kraken), [`coinbase-x402-action-ref-anchor`](https://github.com/giskard09/coinbase-x402-action-ref-anchor)
(Coinbase), [`turnkey-action-ref-anchor`](https://github.com/giskard09/turnkey-action-ref-anchor)
(Turnkey), [`keycard-action-ref-anchor`](https://github.com/giskard09/keycard-action-ref-anchor)
(Keycard), [`pay-kit-action-ref-anchor`](https://github.com/giskard09/pay-kit-action-ref-anchor)
(Solana Foundation pay-kit), [`agent-bounties-action-ref-anchor`](https://github.com/giskard09/agent-bounties-action-ref-anchor)
(agent-bounties).

## License

MIT.
