# Conversation development checks

Automated passes measure response contracts, not answer accuracy.

Run state: complete

| Metric | Value |
|---|---|
| planned_turns | 3 |
| attempted_turns | 3 |
| unattempted_turns | 0 |
| processing_errors | 0 |
| completed_responses | 3 |
| status_matches | 3 |
| status_evaluated | 3 |
| structural_checks_passed | 3 |
| structural_checks_evaluated | 3 |
| answered_responses | 2 |
| answered_with_supported_verdict | 2 |
| withheld_responses | 0 |
| automated_contract_passes | 3 |
| contract_evaluated | 3 |
| mean_completed_latency_seconds | 1.601 |
| median_completed_latency_seconds | 2.077 |
| human_accuracy_review | pending; no automatic accuracy score |

## Manual review

Read results.json for actual histories, complete responses and per-turn review criteria.
Check factual correctness, completeness, intent preservation and appropriate abstention.
The model verifier is not independent ground truth. Human review fields start as null.
