# Fan-in / Adjudication Record Template

Canonical record format for the COMPANY.md "Sealed review protocol". Copy this file per decision; fill every field. A record with blanks is not a record.

## 0. Decision header

- Decision ID:
- Date:
- Research question (identical wording sent to all panelists):
- Orchestrator:

## 1. Sealed panel record (STAGE 1–2)

One row per panelist, filled at dispatch and at return:

| # | Role / agent type | Session ID | Dispatched (time, order) | Return status | Evidence tier | Primary sources inspected | Verdict | Confidence | Unresolved questions |
|---|---|---|---|---|---|---|---|---|---|

Seal rule: a report is SEALED when its return status is SUCCESS or RESEARCH_NEGATIVE and its evidence meets citation standards (else INVALID_EVIDENCE). Only sealed reports advance to STAGE 3.

## 2. Reveal + adversarial synthesis (STAGE 3–4)

- Synthesis session ID:
- Reports revealed (simultaneously): [list]
- Novelty/decision overlap matrix attached: yes/no
- Disagreements preserved verbatim (never averaged):

## 3. Overlap matrix format

Rows = our proposed components; Columns = closest external works; Cells = identical / strong overlap / partial overlap / apparently open / unknown.

| Our component | Work A | Work B | ... |
|---|---|---|---|

## 4. Claim-by-claim evidence ledger

| Claim | Source tier | Primary identifier | Panel verdicts (per panelist) | Post-adjudication status (VERIFIED/LIKELY/UNVERIFIED/CONTRADICTED) | Action on thesis/docs |
|---|---|---|---|---|---|

## 5. Adjudication (STAGE 5)

- Adjudicator session ID (must differ from synthesizer and panelists):
- Primary sources re-inspected by adjudicator:
- Claims materially affecting the thesis, with independent verification outcome:
- Dissents that survive adjudication:
- Adjudicator verdict:
- Orchestrator decision + DECISIONS.md entry reference:

## 6. Statuses vocabulary

SUCCESS · RESEARCH_NEGATIVE · INFRA_FAILURE · PERMISSION_FAILURE · TIMEOUT · INVALID_EVIDENCE (see COMPANY.md). INFRA_FAILURE never counts as research evidence.
