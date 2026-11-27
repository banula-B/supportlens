# Conversation development checks

Automated passes measure response contracts, not answer accuracy.

Run state: complete

| Metric | Value |
|---|---|
| planned_turns | 1 |
| attempted_turns | 1 |
| unattempted_turns | 0 |
| processing_errors | 0 |
| completed_responses | 1 |
| status_matches | 1 |
| status_evaluated | 1 |
| structural_checks_passed | 1 |
| structural_checks_evaluated | 1 |
| answered_responses | 1 |
| answered_with_supported_verdict | 1 |
| withheld_responses | 0 |
| automated_contract_passes | 1 |
| contract_evaluated | 1 |
| mean_completed_latency_seconds | 1.443 |
| median_completed_latency_seconds | 1.443 |
| human_accuracy_review | pending; no automatic accuracy score |

## Manual review

Read results.json for actual histories, complete responses and per-turn review criteria.
Check factual correctness, completeness, intent preservation and appropriate abstention.
The model verifier is not independent ground truth. Human review fields start as null.
