#!/usr/bin/env python3
"""
Produces an action_ref for a synthetic market.near.ai (NEAR AI's Agents
Marketplace) worker assignment `submit`, following action-ref-v1
(argentum-core, JCS RFC 8785 + SHA-256) byte-for-byte, and emits the
artifacts needed to anchor + independently verify it.

PROVENANCE: this is NOT captured from a running worker agent, a real
marketplace account, or any real assignment. The request/response shapes
are modeled on market.near.ai's own public documentation, fetched and read
in full before this script was written:
  - https://market.near.ai/skill/SKILL.md (the worker skill: golden path,
    hard rules, `POST /v1/assignments/{id}/submit`)
  - https://market.near.ai/skill/reference/agent-api.md ("Deliverable rules
    (REST submit)" section: deliverableMarkdown is "stored and hashed by
    the platform")
  - https://market.near.ai/openapi.json (JobAssignment, SubmitRequest,
    DeliverableVersionView schemas)
No claim that NEAR AI or agents-market emits action_ref today, and no claim
of integration, adoption, or endorsement by NEAR AI.
"""
import hashlib
import json
import os
import sys

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
os.makedirs(OUT_DIR, exist_ok=True)


def jcs(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# --- 1. The four required action-ref-v1 preimage fields --------------------
# Per argentum-core/docs/spec/action-ref.md: only these four fields enter the
# hash. assignmentId and the deliverable's own content hash are folded into
# `scope` (same convention every other worked example in this series uses
# for a call-specific identifier the spec itself gives no dedicated field
# for -- see e.g. binance-onchain-pay-action-ref-anchor's
# "network:BASE" suffix). `timestamp` is the real API's own `submittedAt`
# field name and semantics (JobAssignment.submittedAt, ISO 8601).
deliverable_markdown = (
    "# Deliverable: Q3 competitor pricing teardown\n\n"
    "Summary table + sourced notes for the 6 competitors in scope, as "
    "specified in the job brief. Full write-up is linked below; raw sheet "
    "attached as a file per the job's delivery instructions.\n"
)
deliverable_sha256 = sha256_hex(deliverable_markdown)

assignment_id = "018f3b2e-7a4d-7c91-9e2a-worked-example-0001"
timestamp = "2026-10-14T18:32:07.000Z"  # submittedAt

preimage = {
    "agent_id": "worked-example.nearai-agents-market-action-ref-anchor",
    "action_type": "nearai.agents_market.assignment.submit",
    "scope": f"nearai:agents-market:v1/assignments/{{id}}/submit:assignment:{assignment_id}:deliverable_sha256:{deliverable_sha256}",
    "timestamp": timestamp,
}
jcs_payload = jcs(preimage)
action_ref = sha256_hex(jcs_payload)

# --- 2. Additive envelope fields — assignment-specific context -------------
# These do NOT enter the action_ref hash (per action-ref-v1: only the 4
# preimage fields are hashed). They travel alongside as declared context a
# downstream verifier can check independently.
#
# params mirrors SubmitRequest (openapi.json, components.schemas.
# SubmitRequest: required ["deliverableMarkdown"], properties
# deliverableMarkdown/files) plus the JobAssignment fields a worker reads
# from GET /v1/agents/me/assignments right before submitting (assignmentId,
# jobId, workerAgentId, escrowAmount, escrowToken, slaDeadlineAt,
# acceptanceWindowDays — all required fields of JobAssignment per the
# schema). files uses the documented shape ("a fileUrl, bare token or
# fileId").
params = {
    "endpoint": "POST /v1/assignments/{id}/submit",
    "assignmentId": assignment_id,
    "jobId": "018f3b2e-7a4d-7c91-9e2a-worked-example-job1",
    "workerAgentId": "018f3b2e-7a4d-7c91-9e2a-worked-example-agnt",
    "deliverableMarkdown": deliverable_markdown,
    "files": ["https://market.near.ai/files/WORKED-EXAMPLE-TOKEN/pricing-teardown.xlsx"],
    "escrowAmount": "25.000000000000",
    "escrowToken": "USDC",
    "slaDeadlineAt": "2026-10-15T18:32:07.000Z",
    "acceptanceWindowDays": 5,
}
params_digest = sha256_hex(jcs(params))

# result mirrors DeliverableVersionView (openapi.json: required
# ["version", "files", "submittedAt"], properties deliverableHash/
# deliverableUrl/files/senderAgentId/submittedAt/version) — the record the
# platform itself returns from GET /v1/assignments/{id}/deliverable/versions
# after a submit, including the UNDOCUMENTED deliverableHash field (see
# PROVENANCE.md: present in openapi.json with no description anywhere,
# named exactly once in agent-api.md as "stored and hashed by the
# platform" -- no stated algorithm, no stated preimage beyond
# deliverableMarkdown alone, not signed, not bound to assignmentId/jobId/
# the award, and absent from SubmitRequest -- the worker never supplies or
# sees the expected value, only whatever versions.GET later echoes back).
result = {
    "version": 1,
    "deliverableHash": deliverable_sha256,  # same function this worked example uses, declared as an assumption -- see PROVENANCE.md
    "deliverableUrl": None,  # null for an A2A result / text-only Markdown delivery, per the schema's own description
    "files": [
        {"fileUrl": "https://market.near.ai/files/WORKED-EXAMPLE-TOKEN/pricing-teardown.xlsx"}
    ],
    "senderAgentId": "018f3b2e-7a4d-7c91-9e2a-worked-example-agnt",
    "submittedAt": timestamp,
}
result_digest = sha256_hex(jcs(result))

envelope = {
    "packet_version": "1.0",
    "action_ref": action_ref,
    "hash_algo": "sha256",
    "preimage_format": "jcs-rfc8785-v1",
    "preimage": preimage,
    "capability": "agents-market.assignment.submit",
    "params_digest": params_digest,
    "result_digest": result_digest,
    "generated_at_utc": timestamp,
}

manifest = {
    "fixture_id": "nearai-agents-market-assignment-submit-worked-example",
    "spec": "action-ref-v1 (argentum-core, docs/spec/action-ref.md)",
    "preimage": preimage,
    "jcs_payload": jcs_payload,
    "action_ref": action_ref,
    "anchor_ref_bytes32": "0x" + action_ref,
    "anchor_registry": "0x49fEcA52bC634a9Ab773226D16619deC547794aa",
    "anchor_chain": "Base mainnet (chainId 8453)",
    "envelope": envelope,
    "params": params,
    "result": result,
    "provenance": (
        "Synthetic worked example. Request/result shapes modeled on "
        "market.near.ai's own public documentation (/skill/SKILL.md, "
        "/skill/reference/agent-api.md, /openapi.json): SubmitRequest "
        "(deliverableMarkdown, files) and DeliverableVersionView "
        "(version, deliverableHash, deliverableUrl, files, senderAgentId, "
        "submittedAt). NOT captured from a running worker agent, a real "
        "marketplace account, or any real assignment, job, or escrow "
        "payment. assignmentId, jobId, workerAgentId, and the file URL are "
        "synthetic placeholders. deliverableHash here is COMPUTED BY THIS "
        "SCRIPT as SHA-256 of deliverable_markdown, following the one "
        "sentence market.near.ai's own docs give it (\"stored and hashed "
        "by the platform\") -- the platform's exact algorithm, encoding, "
        "and whether files are covered are not publicly specified; see "
        "PROVENANCE.md. No claim that NEAR AI or agents-market emits "
        "action_ref today, and no claim of integration, adoption, or "
        "endorsement by NEAR AI."
    ),
}

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")

print("=== nearai-agents-market-action-ref-anchor : producer ===")
print(f"jcs_payload = {jcs_payload}")
print(f"action_ref  = {action_ref}")
print(f"anchor ref (bytes32) = 0x{action_ref}")
print(f"wrote {OUT_DIR}/manifest.json")
